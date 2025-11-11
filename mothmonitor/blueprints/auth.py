from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import Form, validators, EmailField, PasswordField, BooleanField

from ..models import User
from ..database import db

auth = Blueprint('auth', __name__)

class LoginForm(Form):
    email = EmailField("Email")
    password = PasswordField("Password")
    remember = BooleanField("Remember Me")

@auth.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm(request.form)

    if request.method == 'POST':
        if form.validate():
            email = form.data.get('email')
            password = form.data.get('password')
            remember = form.data.get('remember')

            user = User.query.filter_by(email=email).first()

            if not user or not check_password_hash(user.password, password):
                flash('Please check your login details and try again.')
                return redirect(url_for('auth.login'))
            login_user(user, remember=remember)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Please check your login details and try again.')

    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
