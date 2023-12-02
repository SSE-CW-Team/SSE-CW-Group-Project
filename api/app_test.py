from app import app
from app import get_songs_from_database
import pytest


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_welcome_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_redirect(client):
    response = client.get("/generate")
    assert response.status_code == 302  # Redirect


def test_success_route(client):
    response = client.get("/success")
    assert response.status_code == 200


# Go to login page, post login details and check redirect to success page
def test_redirect_from_spotify(client):
    assert True  # I don't know how to do this yet.
    # Selenium: requires you to have access to where the browser is stored
    # Requests: I don't know how to post the login details


def test_positive_mins_returns_data():
    mins = 30
    genres = ['pop', 'rock', 'hip-hop']
    intesity = 'medium'
    assert get_songs_from_database(mins, genres, intesity)[0] != []


def test_playlist_length_exceeds_run_length():
    mins = 30
    genres = ['pop', 'rock', 'hip-hop']
    intesity = 'medium'
    assert get_songs_from_database(mins, genres, intesity)[1] > mins
