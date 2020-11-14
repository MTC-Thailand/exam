from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, login_required, logout_user
from . import mainbp as main
from .forms import LoginForm
from .models import User


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