from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash

from . import mainbp as main
from .forms import LoginForm, UserForm
from .models import User
from .. import db


@main.route('/')
@login_required
def index():
    return render_template('main/index.html')


@main.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        nextUrl = request.args.get('next')
        if not current_user.is_authenticated:
            if form.validate_on_submit():
                user = User.query.filter_by(username=form.username.data).first()
                if user:
                    status = login_user(user, form.remember_me.data)
                    if status:
                        print(current_user.username)
                        flash('Logged in successfully.', 'success')
                        return redirect(nextUrl or url_for('main.index'))
                    else:
                        flash('Failed to login.', 'danger')
                        return redirect(url_for('main.login'))
                else:
                    flash('User does not exist.', 'danger')
        else:
            if nextUrl:
                return redirect(nextUrl)

    return render_template('main/login.html', form=form)


@main.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    form = UserForm()
    if current_user.email:
        form.email.data = current_user.email
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.password.data == form.confirm.data:
                current_user.password_hash = generate_password_hash(form.password.data)
                current_user.email = form.email.data
                db.session.add(current_user)
                db.session.commit()
                flash('New password has been saved.', 'success')
        else:
            for field, errors in form.errors.items():
                flash('{}'.format(', '.join(errors)), 'danger')
            if not current_user.email:
                form.email.data = ''
    return render_template('main/useraccount.html', form=form)