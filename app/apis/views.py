from http import HTTPStatus
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash

from app.apis.models import ApiClient
from app.apis import api_blueprint as api
from flask_restful import Resource

from app.exambank.models import Specification


@api.route('/test')
def get_access_token_test():
    return jsonify(message='Worked!'), HTTPStatus.OK


@api.route('/token', methods=['POST'])
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


class SpecificationResource(Resource):
    def get(self):
        data = []
        for spec in Specification.query:
            data.append(spec.to_dict())

        return data, HTTPStatus.OK
