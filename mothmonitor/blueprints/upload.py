from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import auth_required
from ..database import db

upload = Blueprint('upload', __name__)

@upload.route('/dashboard')
@auth_required()
def create_key():
    return render_template("upload/create_key.html")
