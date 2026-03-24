from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import auth_required, permissions_required
from ..models import db, Device

devices = Blueprint('devices', __name__)

@devices.route('/list')
@auth_required()
def list():
    devices = db.session.execute(db.select(Device).order_by(Device.id)).scalars()
    return render_template("devices/list.html", **locals())

@devices.route('/edit/', methods=["GET", "POST"], defaults={"device_id": None})
@devices.route('/edit/<device_id>', methods=["GET", "POST"])
@permissions_required("admin")
def device_edit(device_id):
    device = Device(name="")
    if device_id:
        device = db.get_or_404(Device, device_id)
    if request.method == "POST":
        device.label = request.form.get('label')
        if not device_id:
            db.session.add(device)
        db.session.commit()
        return render_template("devices/hx/row.html", **locals())
    return render_template("devices/hx/edit_row.html", **locals())


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

