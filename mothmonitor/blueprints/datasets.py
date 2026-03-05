from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_security import auth_required
from ..models import db, Device, Night
from sqlalchemy.orm import joinedload

import boto3
from botocore.exceptions import ClientError
import dateutil


datasets = Blueprint('datasets', __name__)


DELIM = "/"

def s3_result_prefixes(result, prefix=""):
    prefixes = [f['Prefix'][:-1].replace(prefix, "") for f in result['CommonPrefixes']]
    return prefixes

def get_s3_devices(s3):
    S3_BUCKET = current_app.config['S3_BUCKET']
    result = s3.list_objects(Bucket=S3_BUCKET, Delimiter=DELIM)
    return s3_result_prefixes(result)

def get_s3_device_nights(s3, device):
    S3_BUCKET = current_app.config['S3_BUCKET']
    prefix = f'{device}{DELIM}'
    result = s3.list_objects(Bucket=S3_BUCKET, Delimiter=DELIM,
                             Prefix=prefix)
    return s3_result_prefixes(result, prefix=prefix)

def get_s3_night_files(s3, device, night):
    S3_BUCKET = current_app.config['S3_BUCKET']
    result = s3.list_objects(Bucket=S3_BUCKET, Delimiter=DELIM,
                             Prefix=f'{device_name}{DELIM}')
    print(result)
    return s3_result_prefixes(result)



@datasets.route('/list')
@auth_required()
def list_nights():
    if request.args.get('refresh'):
        nights = refresh_nights_s3()
    else:
        nights = db.session.execute(db.select(Night).options(joinedload(Night.device))).scalars()
    
    return render_template("datasets/list_nights.html", nights=nights)

def refresh_nights_s3():
    nights = []

    s3 = boto3.client("s3")

    try:
        devices = get_s3_devices(s3)
        for device_name in sorted(devices):
            device = db.get_or_create(Device, name=device_name)
            n = get_s3_device_nights(s3, device_name)
            for night_name in sorted(n, reverse=True):
                night_date = dateutil.parser.parse(night_name).date()
                night = db.get_or_create(Night, night=night_date, device_id=device.id)
                nights.append(night)
    except ClientError as e:
        print(f'S3 Error: {e}')
        flash(e, "error")

    return nights
