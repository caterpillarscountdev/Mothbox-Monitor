from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_security import auth_required

import os
import boto3, botocore

from ..models import db, Device


upload = Blueprint('upload', __name__)


def s3_prefix(device, night):
    return os.path.join(device, night)


@upload.route('/')
@auth_required()
def index():
    return render_template('upload/index.html')

@upload.route('/check_manifest', methods=["POST"])
@auth_required()
def check_manifest():
    # TODO: Validate key
    device_key = request.args.get('key')

    S3_BUCKET = current_app.config['S3_BUCKET']
    S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(S3_BUCKET)

    s3 = boto3.client("s3")

    body = request.json
    
    device = body["deviceName"]
    night = body["night"]
    files = body["files"]
    # files = [{"filename": "", "size": 0, "type": "image/jpeg"}]

    prefix = s3_prefix(device, night)
    
    def check_key(filename, size):
        key = f"{prefix}{filename}"
        print(prefix, filename, size)
        return filename, True
        try:
            head = s3.head_object(Bucket=S3_BUCKET, Key=key)
            return filename, (head["ContentLength"] == size)
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                return filename, False
            else:
                raise

    result = {"files": []}
    for f in files:
        url = {}
        filename, missing = check_key(f["filename"], f["size"])
        url["location"] = f"{S3_LOCATION}{filename}"
        if missing:
            url["upload_url"] = create_upload_url(s3, S3_BUCKET, f["filename"], f["type"])
        result["files"].append({
            "filename": filename,
            "missing": missing
        }|url)
            
    return result

def create_upload_url(s3, bucket, file_name, file_type):
    
    return s3.generate_presigned_url(
        "put_object",
        Params = {
            "Bucket": bucket,
            "Key": file_name
        },
        ExpiresIn=3600
    )    
