from flask import Blueprint

mainbp = Blueprint('main', __name__)

from . import views