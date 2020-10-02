from flask import Blueprint

exambank = Blueprint('exambank', __name__)

from . import views