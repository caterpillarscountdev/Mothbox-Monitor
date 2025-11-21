from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import auth_required
from ..models import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template("index.html")

@main.route('/dashboard')
@auth_required()
def dashboard():
    return render_template("dashboard.html")


