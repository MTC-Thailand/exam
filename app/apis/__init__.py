from flask import Blueprint


api_bp = Blueprint('apis', __name__, url_prefix='/apis')

from . import views