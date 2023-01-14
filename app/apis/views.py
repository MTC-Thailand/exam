from http import HTTPStatus
import json
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash

from app.apis.models import ApiClient
from app.apis import api_blueprint as api
from app import csrf
from flask_restful import Resource

from app.exambank.models import Specification


# from app.exambank.models import Specification


@api.route('/test')
def get_access_token_test():
    return jsonify(message='Worked!'), HTTPStatus.OK


@api.route('/token', methods=['POST'])
@csrf.exempt
def get_access_token():
    creds = request.get_json()
    print(request.headers)
    client_id = creds.get('client_id')
    client_secret = creds.get('client_secret')

    client = ApiClient.query.get(client_id)
    if client:
        if check_password_hash(client._secret_hash, client_secret):
            access_token = create_access_token(client.client_id)
            refresh_token = create_refresh_token(client.client_id)
            return jsonify(access_token=access_token, refresh_token=refresh_token)
        else:
            return jsonify(message='Invalid Credentials'), HTTPStatus.BAD_REQUEST
    else:
        return jsonify(message='Error'), HTTPStatus.NOT_FOUND


class SpecificationResource(Resource):
    def get(self):
        data = []
        for spec in Specification.query:
            data.append(spec.to_dict())

        return data, HTTPStatus.OK
