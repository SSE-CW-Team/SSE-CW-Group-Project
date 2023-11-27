from app import app
import pytest


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_welcome_route(client):
    response = client.get('/')
    assert response.status_code == 200


def test_submit_route(client):
    response = client.get('/query')
    assert response.status_code == 200
