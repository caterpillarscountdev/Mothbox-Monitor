from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_security import auth_required
from ..models import db, Device

import boto3


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
    nights = []

    s3 = boto3.client("s3")

    try:
        devices = get_s3_devices(s3)
        for device in sorted(devices):
            # add to db
            n = get_s3_device_nights(s3, device)
            for night in sorted(n, reverse=True):
                # add to db
                print(device, night)
                nights.append({"device": device,
                               "night": night})
    except s3.exceptions.ClientError as e:
        print(f'S3 Error: {e}')
        flash(e, "error")
    
    
    
    return render_template("datasets/list_nights.html", nights=nights)
