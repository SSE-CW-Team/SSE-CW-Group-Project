from app import app
from app import get_songs_from_database
from app import sorting_formula
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
    assert response.status_code == 302  # Redirect


# Unsafe input of HTML tags should be sanitised
def test_unsafe_input_sanitization(client):
    unsafe_name = "<script>alert('Hello world');</script>"
    client.post(
        "/generate", data={"name": unsafe_name, "description": "my_description"}
    )
    # Check that the sanitized name is stored in the session
    with client.session_transaction() as session:
        sanitized_name = session["new_playlist_headers"]["name"]
        assert sanitized_name is not None
    # Verify that the sanitized name does not contain any unsafe HTML
    assert "<script>" not in sanitized_name


bool_flags = {
    "allowExplicit": False,
    "instrumentalOnly": False,
    "includeAcoustic": False,
    "includeLikedSongs": False,
    "includeLive": False,
}


def test_prioritise_tempo():
    # Should choose el1
    slider_values = {
        "popularity": 50.0,
        "tempo": 135.0,
        "energy": 0.2,
        "danceability": 0.0
    }
    el1 = {}
    el1["popularity"] = "50"
    el1["tempo"] = "120"
    el1["energy"] = "0"
    el1["danceability"] = "0"
    el1["liked"] = False
    el2 = {}
    el2["popularity"] = "50"
    el2["tempo"] = "168"
    el2["energy"] = "0.2"
    el2["danceability"] = "0"
    el1["liked"] = False

    el1_priority = sorting_formula(el1, slider_values=slider_values)
    el2_priority = sorting_formula(el2, slider_values=slider_values)
    assert el1_priority > el2_priority


def test_prioritise_tempo_not_too_much():
    # Should choose el2
    slider_values = {
        "popularity": 50.0,
        "tempo": 140.0,
        "energy": 0.2,
        "danceability": 0.0
    }
    el1 = {}
    el1["popularity"] = "50"
    el1["tempo"] = "120"
    el1["energy"] = "0"
    el1["danceability"] = "0"
    el1["liked"] = False
    el2 = {}
    el2["popularity"] = "50"
    el2["tempo"] = "168"
    el2["energy"] = "0.2"
    el2["danceability"] = "0"
    el1["liked"] = False

    el1_priority = sorting_formula(el1, slider_values=slider_values)
    el2_priority = sorting_formula(el2, slider_values=slider_values)
    assert el1_priority < el2_priority


def test_prioritise_liked_songs():
    # Should choose el2
    slider_values = {
        "popularity": 50.0,
        "tempo": 140.0,
        "energy": 0.2,
        "danceability": 0.0
    }
    el1 = {}
    el1["popularity"] = "70"
    el1["tempo"] = "110"
    el1["energy"] = "0.5"
    el1["danceability"] = "0"
    el1["liked"] = True
    el2 = {}
    el2["popularity"] = "60"
    el2["tempo"] = "145"
    el2["energy"] = "0.2"
    el2["danceability"] = "0"
    el2["liked"] = False
    el1_priority = sorting_formula(el1, slider_values=slider_values)
    el2_priority = sorting_formula(el2, slider_values=slider_values)
    assert el1_priority > el2_priority


def test_dont_prioritise_liked_songs_too_much():
    # Should choose el2
    slider_values = {
        "popularity": 50.0,
        "tempo": 140.0,
        "energy": 0.2,
        "danceability": 0.0
    }
    el1 = {}
    el1["popularity"] = "70"
    el1["tempo"] = "100"
    el1["energy"] = "0.8"
    el1["danceability"] = "0.6"
    el1["liked"] = True
    el2 = {}
    el2["popularity"] = "60"
    el2["tempo"] = "145"
    el2["energy"] = "0.2"
    el2["danceability"] = "0"
    el2["liked"] = False
    el1_priority = sorting_formula(el1, slider_values=slider_values)
    el2_priority = sorting_formula(el2, slider_values=slider_values)
    assert el1_priority < el2_priority


def test_positive_mins_returns_data():
    mins = 30
    genres = ["pop", "rock", "hip-hop"]
    slider_values = {"popularity": 74, "tempo": 140, "energy": 0.5, "danceability": 0.5}
    assert get_songs_from_database(mins, genres, slider_values, bool_flags)[0] != []


def test_playlist_length_exceeds_run_length():
    mins = 30
    genres = ["pop", "rock", "hip-hop"]
    slider_values = {"popularity": 74, "tempo": 140, "energy": 0.5, "danceability": 0.5}
    assert get_songs_from_database(mins, genres, slider_values, bool_flags)[1] > mins
