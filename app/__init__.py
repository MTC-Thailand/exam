import os
from functools import wraps

from flask_mail import Message
from flask_admin import Admin, AdminIndexView
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask import Flask, flash, redirect, current_app
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.role == 'admin'


load_dotenv()
db = SQLAlchemy()
migrate = Migrate()
admin = Admin(index_view=MyAdminIndexView())
login = LoginManager()
login.login_view = 'main.login'
csrf = CSRFProtect()
jwt = JWTManager()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = ('MTC-EXAMBANK', os.environ.get('MAIL_USERNAME'))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    db.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app)
    login.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)

    return app


def superuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_authenticated and current_user.role.role == 'admin'):
            flash('You do not have permission to access this page.', 'warning')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


def send_email(to, subject, body):
    msg = Message(subject=subject,
                  body=body,
                  sender=current_app.config.get('mail_username'),
                  recipients=[to])
    mail.send(msg)
