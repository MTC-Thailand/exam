from flask import Blueprint

webadmin = Blueprint('webadmin', __name__)

from . import views