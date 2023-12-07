from app import app
from app import get_songs_from_database
import pytest

sample_data = {
    "run_length": "3.5",
    "selectedGenres": "Rock, Pop",
    "intensity": "high",
    "name": "My Playlist",
    "description": "A great playlist",
    "tempoValue": "100",
    "energyValue": "0.5",
    "danceabilityValue": "0.5",
    "popularityValue": "70",
}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_welcome_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_redirect(client):
    response = client.post(
        "/generate", data={"name": "my_name", "description": "my_description"}
    )
    assert response.status_code == 302  # Redirect


def test_fetch_songs_redirect(client):
    response = client.post("/fetch_songs", data=sample_data)
    assert response.status_code == 302


def test_success_route(client):
    response = client.get("/success")
    assert response.status_code == 200


def test_positive_mins_returns_data():
    mins = 30
    genres = ["pop", "rock", "hip-hop"]
    slider_values = {"popularity": 74, "tempo": 140, "energy": 0.5}
    bool_flags = {
        "allowExplicit": False,
        "instrumentalOnly": False,
        "includeAcoustic": False,
        "includeLikedSongs": False,
        "includeLive": False,
    }
    assert get_songs_from_database(mins, genres, slider_values, bool_flags)[0] != []


def test_playlist_length_exceeds_run_length():
    mins = 30
    genres = ["pop", "rock", "hip-hop"]
    slider_values = {"popularity": 74, "tempo": 140, "energy": 0.5}
    bool_flags = {
        "allowExplicit": False,
        "instrumentalOnly": False,
        "includeAcoustic": False,
        "includeLikedSongs": False,
        "includeLive": False,
    }
    assert get_songs_from_database(mins, genres, slider_values, bool_flags)[1] > mins
