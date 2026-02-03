import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_security import permissions_required, current_user
from ..models import db, User, Role

users = Blueprint('users', __name__)

@users.route('/manage')
@permissions_required("admin")
def manage_users():
    print("current user", current_user)
    users = db.session.execute(db.select(User).order_by(User.id)).scalars()
    return render_template("users/manage_users.html", **locals())


@users.route('/manage/edit/', methods=["GET", "POST"], defaults={"user_id": None})
@users.route('/manage/edit/<user_id>', methods=["GET", "POST"])
@permissions_required("admin")
def manage_users_edit(user_id):
    user = User(name="", email="", active=True)
    if user_id:
        user = db.get_or_404(User, user_id)
    roles = db.session.execute(db.select(Role).order_by(Role.name)).scalars()
    if request.method == "POST":
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.active = request.form.get('active', False) and True
        rids = {r.id: r for r in roles}
        user.roles = [rids[int(x)] for x in request.form.getlist('roles')]
        if not user_id:
            user.fs_uniquifier = uuid.uuid4().hex 
            db.session.add(user)
        db.session.commit()
        return render_template("users/hx/manage_users_row.html", **locals())
    return render_template("users/hx/manage_users_edit.html", **locals())
