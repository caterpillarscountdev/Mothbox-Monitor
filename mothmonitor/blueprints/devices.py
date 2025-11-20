from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import auth_required
from ..models import db, User

devices = Blueprint('devices', __name__)

@devices.route('/list')
@auth_required()
def list():
    return render_template("devices/list.html")

@devices.route('/create_key', defaults={"device": None}, methods=["POST"])
@devices.route('/create_key/<device>', methods=["POST"])
@auth_required()
def create_key(device):
    return render_template("devices/hx/create_key.html", **locals())
