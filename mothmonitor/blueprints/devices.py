from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_security import auth_required, permissions_required
from flask_cors import cross_origin

import json

from ..models import db, Device, User, Role

devices = Blueprint('devices', __name__)

days_of_week = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

@devices.app_template_filter()
def config_schedule(config, format="full"):
    if type(config) is str:
        config = json.loads(config)
    
    if config and config["schedule"]:
        days = [days_of_week[int(x)-1] for x in config["schedule"]["weekday"].split(";")]
        hours = [f'{int(x):02}:{int(config["schedule"]["minute"]):02}' for x in config["schedule"]["hour"].split(";")]
        runtime = config["schedule"]["runtime"]
        if format == "full":
            return  f'{", ".join(days)}</em><br> at <em class="status-label">{ ", ".join(hours)}</em><br> every <em class="status-label">{config["schedule"]["camera_interval"]}</em> min for <em class="status-label">{runtime}</em> min with {config["schedule"].get("attracttwo", None) and "two strips" or "one strip"}'
        elif format == "small":
            return f'{len(days)} days of {len(hours)*runtime/60:.1f} hrs'
    else:
        return "N/A"

@devices.route('/list')
@auth_required()
def list_devices():
    devices = db.session.execute(db.select(Device).order_by(Device.id)).scalars()
    return render_template("devices/list.html", **locals())

@devices.route('/show/<device_id>')
@permissions_required("admin")
def device_show(device_id):
    if device_id:
        device = db.get_or_404(Device, device_id)
    return render_template("devices/hx/row.html", **locals())


@devices.route('/edit/', methods=["GET", "POST"], defaults={"device_id": None})
@devices.route('/edit/<device_id>', methods=["GET", "POST"])
@permissions_required("admin")
def device_edit(device_id):
    device = Device(name="")
    if device_id:
        device = db.get_or_404(Device, device_id)
    users = list(db.session.execute(db.select(User).where(User.roles.any(Role.name=='Site'))).scalars())
    user_count = len(users)
    if request.method == "POST":
        device.label = request.form.get('label')
        user_ids = request.form.getlist('site_users')
        if user_ids:
            device.site_users = list(db.session.execute(db.select(User).filter(User.id.in_(user_ids))).scalars())
        else:
            device.site_users = []
        if not device_id:
            db.session.add(device)
        db.session.commit()
        return render_template("devices/hx/row.html", **locals())
    return render_template("devices/hx/edit_row.html", **locals())


@devices.route('/detail/<device_id>', methods=["GET", "POST"])
@permissions_required("admin")
def device_detail(device_id):
    if device_id:
        device = db.get_or_404(Device, device_id)
    if type(device.remote_config) is str:
        config = json.loads(device.remote_config)
    else:
        config = device.remote_config
    return render_template("devices/hx/detail_row.html", **locals())


@devices.route('/empty')
def empty():
    return ""


@devices.route('/create_key', defaults={"device_id": None}, methods=["POST"])
@devices.route('/create_key/<device_id>', methods=["POST"])
@auth_required()
def create_key(device_id):
    device = Device(name="")
    if device_id:
        device = db.get_or_404(Device, device_id)
    else:
        db.session.add(device)
    device.generate_upload_key()
    db.session.commit()
    return render_template("devices/hx/row.html", **locals())

@devices.route('/check_config', methods=["POST"])
@cross_origin()
def check_config():
    device_key = request.args.get('key')
    valid_device = Device.check_device_key(device_key)
    if not valid_device:
        abort(401)

    body = request.json

    response = {"received": []}

    if body.get('code_version'):
        valid_device.code_version = body["code_version"]
        response["received"].append("code_version")
    if body.get('config'):
        valid_device.remote_config = body["config"]
        response["received"].append("config")
    if body.get('recent_logs'):
        valid_device.recent_logs = body["recent_logs"]
        response["received"].append("recent_logs")

    if valid_device.updated_config:
        check = deep_update({}, valid_device.remote_config, valid_device.updated_config)
        if check == valid_device.remote_config:
            # Updates have been applied
            valid_device.updated_config = None
        else:
            response["updated_config"] = valid_device.updated_config

    db.session.commit()
    
    return response


import collections.abc

def deep_update(d, *ups):
    for u in ups:
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = deep_update(d.get(k, {}), v)
            else:
                d[k] = v
    return d
