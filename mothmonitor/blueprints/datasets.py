from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_security import permissions_required, auth_required, current_user

from sqlalchemy.orm import joinedload, attributes

import copy
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import dateutil
import mimetypes
from NamedAtomicLock import NamedAtomicLock

from ..models import db, Device, Night, User
from .. import antenna


datasets = Blueprint('datasets', __name__)

NIGHT_LOCK = NamedAtomicLock("refresh_nights", maxLockAge=30)
SYNC_LOCK = NamedAtomicLock("sync_nights", maxLockAge=30)
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

    def get_night_metadata_json(self, device_name, night_name):
        S3_BUCKET = current_app.config['S3_BUCKET']
        try:
            result = self.s3.get_object(Bucket=S3_BUCKET,
                                        Key=f'{device_name}{DELIM}{night_name}{DELIM}metadata.json')
        except self.s3.exceptions.NoSuchKey as e:
            return None
        return json.loads(result["Body"].read().decode('utf-8'))
        

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
    forced_refresh = request.args.get('refresh')
    if forced_refresh or has_stale_night():
         refresh_nights_s3(forced_refresh=forced_refresh)

    try:
        syncs = sync_nights_antenna()
        if len(syncs):
            flash(f"Syncing {len(syncs)} stations on Antenna", "ok")
    except antenna.APIError as e:
        flash(f"{e}", "error")
         
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
    if current_user.can("site") and not current_user.can("research"):
        ids = [x.id for x in current_user.site_devices]
        # restrict query to assigned devices
        select = select.join(Night.device).filter(Device.id.in_(ids))

    filters = { k: request.args.get(k) for k in request.args.keys() if k.startswith("f_") }
    if filters:
        if filters.get("f_attract"):
            select = select.filter(Night.config[("parsed", "attracts")].as_integer() == int(filters.get("f_attract")))
        if filters.get("f_sessions"):
            select = select.filter(Night.config[("parsed", "num_hours")].as_integer() == int(filters.get("f_sessions")))
        if filters.get("f_min_hours"):
            select = select.filter(Night.config[("parsed", "total_hours")].as_float() >= float(filters.get("f_min_hours")))
        if filters.get("f_min_photos"):
            select = select.filter(Night.photo_count >= int(filters.get("f_min_photos")))

    nights = db.paginate(select, per_page=20, error_out=False)

    if nights.page != 1 and len(nights.items) == 0:
        return redirect(url_for(request.endpoint, page=1))

    return render_template("datasets/list_nights.html", nights=nights, sort=sort, sort_asc=sort_asc, station_url=antenna.station_url)

def has_stale_night():
    return db.session.execute(db.select(Device).where(Device.last_refreshed<Device.last_seen)).scalars().first()

def sync_nights_antenna():
    syncs = []
    if SYNC_LOCK.acquire(timeout=2):
        try:
            syncs = antenna.sync_stale_deployments()
        finally:
            SYNC_LOCK.release()
    return syncs

def refresh_nights_s3(**kwargs):
    if NIGHT_LOCK.acquire(timeout=2):
        try:
            _refresh_nights_s3(**kwargs)
        finally:
            NIGHT_LOCK.release()
    

def _refresh_nights_s3(forced_refresh=False):
    if not has_stale_night() and not forced_refresh:
        # Skip if we've been waiting for lock and another process has completed.
        return
    
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
                if photo_count < 1:
                    continue
                last_photo = photos[-1]["filename"]
                last_modified = photos[-1]["lastModified"]
                config = s3.get_night_metadata_json(device_name, night_name)
                night_date = dateutil.parser.parse(night_name).date()
                night = db.get_or_create(Night,
                                         night=night_date,
                                         device_id=device.id)
                
                night.photo_count = photo_count
                night.last_modified = last_modified
                night.last_photo = last_photo
                night.config = config_parsed(config)
                
                nights.append(night)
        db.session.commit()
    except ClientError as e:
        print(f'S3 Error: {e}')
        flash(e, "error")

    return nights

def config_parsed(config):
    '''Parse some of the config to be queryable in JSON'''
    cfg = config["parsed"] = {}
    if not config.get("schedule"):
        return config
    cfg["days"] = [int(x) for x in config["schedule"]["weekday"].split(";")]
    cfg["hours"] = [int(x) for x in config["schedule"]["hour"].split(";")]
    cfg["attracts"] = 1
    if str(config["schedule"].get("attracttwo", None)).lower() in ["1", "true"]:
        cfg["attracts"] = 2
    cfg["num_hours"] = len(cfg["hours"])
    cfg["num_days"] = len(cfg["days"])
    cfg["total_hours"] = len(cfg["hours"])*config["schedule"]["runtime"]/60
    return config

@datasets.route("/_migrate/config_parsed")
@permissions_required("admin")
def migrate_config_parsed():

    for night in db.session.execute(db.select(Night)).scalars():
        night.config = config_parsed(night.config or {})
        attributes.flag_modified(night, "config")
    db.session.commit()
    return "ok"
