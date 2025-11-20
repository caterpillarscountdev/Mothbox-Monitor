from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import auth_required
from ..models import db, User, Role

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


@main.route('/users-manage/edit/', methods=["GET", "POST"], defaults={"user_id": None})
@main.route('/users-manage/edit/<user_id>', methods=["GET", "POST"])
@auth_required()
def manage_users_edit(user_id):
    user = User(name="", email="", active=True)
    if user_id:
        user = db.get_or_404(User, user_id)
    roles = db.session.execute(db.select(Role).order_by(Role.name)).scalars()
    if request.method == "POST":
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.active = request.form.get('active', False) and True
        if not user_id:
            db.session.add(user)
        db.session.commit()
        return render_template("hx/manage_users_row.html", **locals())
    return render_template("hx/manage_users_edit.html", **locals())
