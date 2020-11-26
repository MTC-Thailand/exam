import os
from functools import wraps

from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask import Flask, flash, redirect
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()
migrate = Migrate()
admin = Admin()
login = LoginManager()
login.login_view = 'main.login'
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    db.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app)
    login.init_app(app)
    csrf.init_app(app)

    return app


def superuser(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.role != 'adminview':
            flash('You do not have permission to access this page.', 'warning')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function