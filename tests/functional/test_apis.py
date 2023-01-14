from http import HTTPStatus
import json

from flask import url_for

from app import create_app


def test_getting_an_access_token_test(test_client):
    resp = test_client.get('/apis/test')
    assert resp.status_code == HTTPStatus.OK


def test_getting_an_access_token_no_credentials(test_client):
    resp = test_client.post('/apis/token')
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_getting_an_access_token(test_client):
    client_id = '5824863272'
    client_secret = 'o1Cw2a82RCd6hUP4SfTD3GKVUJtxmg3V'
    resp = test_client.post('/apis/token', json=dict(client_id=client_id,
                                                     client_secret=client_secret))
    assert resp.status_code == HTTPStatus.OK
    # assert 'access_token' in resp.json()
    # assert 'refresh_token' in resp.json()
