from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_security import auth_required
from ..models import db, Device, Night
from sqlalchemy.orm import joinedload

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import dateutil
import mimetypes


datasets = Blueprint('datasets', __name__)


DELIM = "/"


class S3Reader:
    def __init__(self, s3):
        self.s3 = s3
    
    def result_prefixes(self, result, prefix=""):
        prefixes = [f['Prefix'][:-1].replace(prefix, "") for f in result.get('CommonPrefixes', None)]
        return prefixes

    def result_file_contents(self, result):
        return [{"filename": f["Key"],
                 "size": f["Size"],
                 "type": mimetypes.guess_type(f["Key"])[0],
                 "lastModified": f["LastModified"]
                 }
                for f in result["Contents"]]

    def get_devices(self):
        S3_BUCKET = current_app.config['S3_BUCKET']
        result = self.s3.list_objects(Bucket=S3_BUCKET, Delimiter=DELIM)
        return self.result_prefixes(result)

    def get_device_nights(self, device):
        S3_BUCKET = current_app.config['S3_BUCKET']
        prefix = f'{device}{DELIM}'
        result = self.s3.list_objects(Bucket=S3_BUCKET, Delimiter=DELIM,
                                 Prefix=prefix)
        return self.result_prefixes(result, prefix=prefix)

    def get_night_files(self, device_name, night_name):
        S3_BUCKET = current_app.config['S3_BUCKET']
        result = self.s3.list_objects(Bucket=S3_BUCKET, Delimiter=DELIM,
                                 Prefix=f'{device_name}{DELIM}{night_name}{DELIM}')
        return self.result_file_contents(result)

@datasets.route('/detail/<night_id>')
@auth_required()
def night_detail(night_id):

    night = db.get_or_404(Night, night_id)
    if night.last_photo:
        last_photo_url = s3_read_url(current_app.config['S3_BUCKET'], night.last_photo)
    return render_template("datasets/hx/detail_row.html", **locals())

def s3_read_url(bucket, key, expires_in=3600):
    s3 = boto3.client("s3")
    return s3.generate_presigned_url(
        "get_object",
        Params = {
            "Bucket": bucket,
            "Key": key
        },
        ExpiresIn=3600
    )    
    


@datasets.route('/list')
@auth_required()
def list_nights():
    stale_night = db.session.execute(db.select(Device).where(Device.last_refreshed<Device.last_seen)).scalars().first()
    if request.args.get('refresh') or stale_night:
         refresh_nights_s3()

    sort = request.args.get('sort', 'last_modified')
    sort_asc = request.args.get('asc', False)

    select = db.select(Night).options(joinedload(Night.device))
    sorts = []
    if sort:
        sorter = getattr(Night, sort)
        if not sort_asc:
            sorter = sorter.desc()
        sorts.append(sorter)
        if sort == 'device_id':
            sorts.append(Night.night.desc())
        select = select.order_by(*sorts)
    
    nights = db.paginate(select, per_page=20, error_out=False)

    if nights.page != 1 and len(nights.items) == 0:
        return redirect(url_for(request.endpoint, page=1))

    return render_template("datasets/list_nights.html", nights=nights, sort=sort, sort_asc=sort_asc)

def refresh_nights_s3():
    nights = []

    s3 = S3Reader(boto3.client("s3"))

    try:
        devices = s3.get_devices()
        for device_name in sorted(devices):
            device = db.get_or_create(Device, name=device_name)
            device.last_refreshed = datetime.now()
            n = s3.get_device_nights(device_name)
            for night_name in sorted(n, reverse=True):
                files = s3.get_night_files(device_name, night_name)
                photos = [f for f in files if f["type"] == 'image/jpeg']
                photos = sorted(photos, key=lambda x: x["lastModified"])
                photo_count = len(photos)
                last_photo = photos[-1]["filename"]
                last_modified = photos[-1]["lastModified"]
                night_date = dateutil.parser.parse(night_name).date()
                night = db.get_or_create(Night,
                                         night=night_date,
                                         device_id=device.id)
                
                night.photo_count = photo_count
                night.last_modified = last_modified
                night.last_photo = last_photo
                
                nights.append(night)
        db.session.commit()
    except ClientError as e:
        print(f'S3 Error: {e}')
        flash(e, "error")

    return nights
