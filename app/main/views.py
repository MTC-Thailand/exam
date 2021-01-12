from collections import defaultdict
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app import send_email
from . import mainbp as main
from .forms import LoginForm, UserForm, ResetPasswordForm, NewPasswordForm
from .models import User
from app.exambank.models import Item
from .. import db


@main.route('/')
@login_required
def index():
    submitted_items = defaultdict(int)
    items = defaultdict(int)
    for item in Item.query.all():
        items[item.status] += 1
        if item.status == 'submit':
            submitted_items[item.bank.subject.name] += 1

    submitted_items = [pair for pair in submitted_items.items()]
    submitted_items = [['Subject', 'Count']] + submitted_items
    items = [pair for pair in items.items()]
    items = [['Status', 'Count']] + items
    return render_template('main/index.html', items=items, submitted_items=submitted_items)


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
                    if user.verify_password(form.password.data):
                        status = login_user(user, form.remember_me.data)
                        if status:
                            print(current_user.username)
                            flash('Logged in successfully.', 'success')
                            return redirect(nextUrl or url_for('main.index'))
                        else:
                            flash('Failed to login.', 'danger')
                            return redirect(url_for('main.login'))
                    else:
                        flash('Password is not correct.', 'danger')
                else:
                    flash('User does not exist.', 'danger')
        else:
            if nextUrl:
                return redirect(nextUrl)

    return render_template('main/login.html', form=form)


@main.route('/set-password', methods=['GET', 'POST'])
def set_password():
    form = NewPasswordForm()
    s = Serializer(current_app.config.get('SECRET_KEY'))
    token = s.loads(request.args.get('token'))
    mail = token.get('email')
    if request.method == 'GET':
        if mail:
            return render_template('main/set_password.html', form=form)
        else:
            return 'Bad access token.'

    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=mail).first()
            if user:
                if form.password.data == form.confirm.data:
                    user.password = form.password.data
                    db.session.add(user)
                    db.session.commit()
                    flash('Password changed, please try to log in.', 'success')
                    return redirect(url_for('main.login'))
                else:
                    flash('Password must match.'.format(mail), 'danger')
            else:
                flash('Cannot find the user with e-mail address = {}.'\
                      .format(mail), 'warning')


@main.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if not user:
                flash('ไม่พบอีเมลที่ระบุในฐานข้อมูล', 'warning')
            else:
                s = Serializer(current_app.config.get('SECRET_KEY'), 3600)
                token = s.dumps({'email': form.email.data})
                body = 'Click the link to reset your password. {}'\
                    .format(url_for('main.set_password',
                                    token=token,
                                    _external=True))
                send_email(to=user.email, subject='Password Reset', body=body)
                flash('Link to reset a password has been sent to {}.'\
                      .format(form.email.data), 'warning')
                return redirect(url_for('main.index'))
    return render_template('main/reset_password.html', form=form)


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