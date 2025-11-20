from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import auth_required
from ..models import db, User

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template("index.html")

@main.route('/dashboard')
@auth_required()
def dashboard():
    return render_template("dashboard.html")


@main.route('/users-manage')
@auth_required()
def manage_users():
    
    users = db.session.execute(db.select(User).order_by(User.id)).scalars()
    return render_template("manage_users.html", **locals())

@main.route('/users-manage/<user_id>', methods=["GET", "POST"])
@auth_required()
def manage_users_edit(user_id):
    user = db.get_or_404(User, user_id)
    if request.method == "POST":
        pass
    return render_template("manage_users_edit.html", **locals())
