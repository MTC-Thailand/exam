from http import HTTPStatus

from flask import url_for

from app import create_app
from app.apis import api_bp as api_blueprint


def test_getting_an_access_token_test():
    flask_app = create_app()
    flask_app.register_blueprint(api_blueprint)

    with flask_app.test_client() as test_client:
        resp = test_client.get('/apis/test')
        assert resp.status_code == HTTPStatus.OK


def test_getting_an_access_token_no_credentials():
    flask_app = create_app()
    flask_app.register_blueprint(api_blueprint)

    with flask_app.test_client() as test_client:
        resp = test_client.post('/apis/token')
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_getting_an_access_token():
    flask_app = create_app()

    with flask_app.test_client() as test_client:
        client_id = '6685647115'
        client_secret = 'kp7hejw7QfEnYEl5HelfU3hKoRqkn0gR'
        resp = test_client.post('/apis/token',
                                json=dict(client_id=client_id,
                                          client_secret=client_secret))
        assert resp.status_code == HTTPStatus.OK
        assert 'access_token' in resp.json()
        assert 'refresh_token' in resp.json()
