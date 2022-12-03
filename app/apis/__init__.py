from flask import Blueprint

api_blueprint = Blueprint('apis', __name__, url_prefix='/apis')


from . import views