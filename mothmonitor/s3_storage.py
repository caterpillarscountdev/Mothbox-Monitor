import json
import boto3
from datetime import datetime
import dateutil
import mimetypes

from botocore.exceptions import ClientError

from flask import current_app

from .models import db, Device, Night, has_stale_night
from .jobs import enqueue_one

DELIM = "/"

class S3Reader:
    def __init__(self):
        self.s3 = boto3.client("s3")
    
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

    def read_url(self, bucket, key, expires_in=3600):
        return self.s3.generate_presigned_url(
            "get_object",
            Params = {
                "Bucket": bucket,
                "Key": key
            },
            ExpiresIn=3600
        )    

    def refresh_nights(self, forced_refresh=False):
        if not has_stale_night() and not forced_refresh:
            # Skip if we've been waiting for lock and another process has completed.
            return
    
        nights = []

        try:
            devices = self.get_devices()
            for device_name in sorted(devices):
                device = db.get_or_create(Device, name=device_name)
                device.last_refreshed = datetime.now()
                n = self.get_device_nights(device_name)
                for night_name in sorted(n, reverse=True):
                    files = self.get_night_files(device_name, night_name)
                    photos = [f for f in files if f["type"] == 'image/jpeg']
                    photos = sorted(photos, key=lambda x: x["lastModified"])
                    photo_count = len(photos)
                    if photo_count < 1:
                        continue
                    last_photo = photos[-1]["filename"]
                    last_modified = photos[-1]["lastModified"]
                    config = self.get_night_metadata_json(device_name, night_name)
                    night_date = dateutil.parser.parse(night_name).date()
                    night = db.get_or_create(Night,
                                             night=night_date,
                                             device_id=device.id)

                    night.photo_count = photo_count
                    night.last_modified = last_modified
                    night.last_photo = last_photo
                    night.config = config_parsed(config or {})

                    nights.append(night)
            db.session.commit()
        except ClientError as e:
            print(f'S3 Error: {e}')

def refresh_nights(**kwargs):
    S3Reader().refresh_nights(**kwargs)

def enqueue_refresh_nights(**kwargs):
    return enqueue_one(refresh_nights, **kwargs)
    
def config_parsed(config):
    '''Parse some of the config to be queryable in JSON'''
    cfg = config.get("parsed", {})
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
    config["parsed"] = cfg
    return config
