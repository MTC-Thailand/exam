import pytest
from app import create_app


@pytest.fixture
def app():
    flask_app = create_app()

    from app.apis import api_blueprint
    flask_app.register_blueprint(api_blueprint)

    return flask_app


@pytest.fixture
def test_client(app):
    yield app.test_client()
