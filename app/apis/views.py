from http import HTTPStatus

from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash

from app.apis import api_bp as apis
from app.apis.models import ApiClient


@apis.route('/test')
def get_access_token_test():
    return jsonify(message='Worked!'), HTTPStatus.OK


@apis.route('/token', methods=['POST'])
def get_access_token():
    client_id = request.json.get('client_id')
    client_secret = request.json.get('client_secret')

    client = ApiClient.query.get(client_id)
    if client:
        if check_password_hash(client_secret, client._secret_hash):
            access_token = create_access_token(client.id)
            refresh_token = create_refresh_token(client.id)
            return jsonify(access_token=access_token, refresh_token=refresh_token)
    else:
        return jsonify(message='Error'), HTTPStatus.INTERNAL_SERVER_ERROR