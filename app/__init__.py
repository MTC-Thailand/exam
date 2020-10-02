import os
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()
migrate = Migrate()
admin = Admin()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    db.init_app(app)
    migrate.init_app(app, db)
    admin.init_app(app)

    return app
