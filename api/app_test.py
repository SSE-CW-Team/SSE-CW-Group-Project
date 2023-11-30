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


def test_login_redirect(client):
    response = client.get('/generate')
    assert response.status_code == 302  # Redirect


def test_success_route(client):
    response = client.get('/success')
    assert response.status_code == 200


# Go to login page, post login details and check redirect to success page
def test_redirect_from_spotify(client):
    assert True  # I don't know how to do this yet.
    # Selenium: requires you to have access to where the browser is stored
    # Requests: I don't know how to post the login details
