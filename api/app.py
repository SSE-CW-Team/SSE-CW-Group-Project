from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from spotipy.oauth2 import SpotifyOAuth  # type: ignore
from spotipy import Spotify  # type: ignore
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import timedelta
import bleach  # type: ignore
import os

load_dotenv()

app = Flask(__name__)

client_id = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]
app.secret_key = os.environ["SECRET_KEY"]

# Set lifetime of session, to prevent session hijacking
app.permanent_session_lifetime = timedelta(minutes=10)

# Initialize the Supabase client with project URL and public API key
supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_ANON_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

scopes = [  # The amount of access to the account that Spotify allows us
    "playlist-modify-public",
    "playlist-modify-private",
]


@app.route("/")
def index():
    return render_template("index.html")


def get_songs_from_database(run_length_in_minutes, genres, slider_values, bool_flags):
    # Variables
    run_length_ms = run_length_in_minutes * 60000

    # Construct base query
    query = (
        supabase.table("spotify_database")
        .select("*")  # Select all fields to compute scores later
        .in_("track_genre", genres)
    )

    # Add conditions based on boolean flags
    if bool_flags["excludeExplicit"]:
        query = query.eq("explicit", False)

    if bool_flags["instrumentalOnly"]:
        query = query.gte("instrumentalness", 0.8)

    if bool_flags["excludeAcoustic"]:
        query = query.lte("acousticness", 0.8)

    if bool_flags["excludeLive"]:
        query = query.gte("liveness", 0.8)

    # Execute query
    response = query.execute()
    data = response.data

    # Print the constructed SQL query
    print("Returned Data:", response.data)

    # Function to normalize values
    def normalize(value, max_value):
        return float(value) / max_value

    # Function to compute fit score from sliding scale inputs
    def compute_score(song):
        score = 0
        for attribute, (user_value, max_value, importance_weighting) in slider_values.items():
            # Convert song's attribute value to float if it's a string
            song_value = float(song[attribute]) if isinstance(song[attribute], str) else song[attribute]
            song_value_normalized = normalize(song_value, max_value)
            user_value_normalized = normalize(user_value, max_value)
            score += (1 - abs(song_value_normalized - user_value_normalized)) * importance_weighting
        return score # Higher score is better

    # Compute scores for each song
    scored_songs = [(song, compute_score(song)) for song in data]

    # Sort songs by score, descending order
    scored_songs.sort(key=lambda x: x[1], reverse=True)

    # Select songs based on run length and score
    track_ids = []
    total_duration = 0
    for song, score in scored_songs:
        if total_duration + song["duration_ms"] <= run_length_ms:
            track_ids.append(song["track_id"])
            total_duration += song["duration_ms"]
        else:
            break
    return selected, total_duration


@app.route("/fetch_songs", methods=["POST"])
def fetch_songs():
    run_length = float(request.form.get("run_length"))
    genres = string_to_list(request.form.get("selectedGenres"))

    # Dictionary for slider values and thresholds
    slider_values = {
        "energy": float(request.form.get("energyValue")),
        "popularity": float(request.form.get("popularityValue")),
        "danceability": float(request.form.get("danceabilityValue")),
        "tempo": float(request.form.get("tempoValue")),
    }

    # Dictionary for boolean flags
    bool_flags = {
        "allowExplicit": request.form.get("allowExplicit") == "true",
        "instrumentalOnly": request.form.get("instrumentalOnly") == "true",
        "includeAcoustic": request.form.get("includeAcoustic") == "true",
        "includeLive": request.form.get("includeLive") == "true",
    }

    song_data = get_songs_from_database(run_length, genres, slider_values, bool_flags)[
        0
    ]
    session["track_ids"] = [i["track_id"] for i in song_data]
    session["titles"] = [i["track_name"] for i in song_data]
    session["artists"] = [i["artists"].replace(";", ", ") for i in song_data]
    session["lengths"] = [
        seconds_to_mm_ss(int(i["duration_ms"] / 1000)) for i in song_data
    ]

    print(session["lengths"])

    if not genres[0]:  # No genre selected
        flash("Please select at least one genre")
        return redirect(url_for("index", _external=True))
    else:
        return redirect(url_for("export", _external=True))


@app.route("/export")
def export():
    return render_template("export.html")


# Request Spotify to log the user in
@app.route("/generate", methods=["POST", "GET"])
def generate():
    session.permanent = True
    sp_oauth = get_spotify_oauth()
    # The authorise_url is where Spotify redirects you once
    # it's finished logging you in. This should be set in our app
    # on the Spotify developers site as both
    # https://localhost:5000/redirect (for testing) and
    # https://sse-cw-group-project.vercel.app/redirect (for deployment)
    authorise_url = sp_oauth.get_authorize_url()
    return redirect(authorise_url)


# The user never actually sees this page.
# This is just where the token info is collected
@app.route("/redirect")
def _redirect():
    sp_oauth = get_spotify_oauth()
    try:
        session.pop("token info")
    except KeyError:
        pass
    code = request.args.get("code", None)  # returns None if request fails
    token_info = sp_oauth.get_access_token(code)
    session["token info"] = token_info  # needed for refreshing token
    return redirect(url_for("create_playlist", _external=True))


@app.route("/create_playlist")  # probably doesn't need its own url
def create_playlist():
    # INITIALISE THE PLAYLIST
    token_info = session.get("token info", None)
    sp = Spotify(auth=token_info["access_token"])
    user_info = sp.me()
    user_id = user_info["id"]
    try:
        sp.user_playlist_create(
            user_id,
            name=session['new_playlist_headers']['name'],
            description=session['new_playlist_headers']['description']
        )
    except Exception as e:
        return "Error creating playlist: " + str(e)
    # Check that this is the right playlist
    last_playlist_id = sp.user_playlists(user_id)["items"][0]["id"]
    # ADD ITEMS TO PLAYLIST
    ids_to_add = session.get("track_ids")[0]
    try:
        sp.playlist_add_items(last_playlist_id, ids_to_add)
    except Exception:
        return "Error adding songs to playlist"
    return redirect(url_for("success", _external=True))


def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for("_redirect", _external=True),
        scope=scopes,
    )


# Page that links you to Spotify. Maybe it could contain a link
# to your playlist instead?
@app.route("/success", methods=["GET"])
def success():
    return render_template("success.html")


@app.route("/fetch_songs", methods=["POST"])
def fetch_songs():
    run_length = float(request.form.get("run_length"))
    genres = string_to_list(request.form.get("selectedGenres"))

    # Print data received from form
    print("Received form data:", request.form)

    # Dictionary for slider values and corresponding max values
    slider_values = {   # (input_value, max_possible_value, importance_weighting)
        "energy": (float(request.form.get("energyValue")), 1, 1),
        "popularity": (float(request.form.get("popularityValue")), 100, 1),
        "danceability": (float(request.form.get("danceabilityValue")), 1, 1),
        "tempo": (float(request.form.get("tempoValue")), 220, 1)
    }

    # Dictionary for boolean flags
    bool_flags = {
        "excludeExplicit": request.form.get("excludeExplicit") == 'true',
        "instrumentalOnly": request.form.get("instrumentalOnly") == 'true',
        "excludeAcoustic": request.form.get("excludeAcoustic") == 'true',
        "excludeLive": request.form.get("excludeLive") == 'true'
    }

    session['new_playlist_headers'] = {
        'name': bleach.clean(request.form.get("name", "")),
        'description': bleach.clean(request.form.get("description", ""))
    }

    track_ids, total_duration = get_songs_from_database(run_length, genres, slider_values, bool_flags)
    session["track_ids"] = track_ids

    if not genres[0]:  # No genre selected
        flash("Please select at least one genre")
        return redirect(url_for('index', _external=True))
    else:
        return redirect(url_for("success", _external=True))


def string_to_list(input_string):
    result_list = input_string.split(", ")
    result_list = [item.strip().lower() for item in result_list]
    return result_list


def seconds_to_mm_ss(seconds):
    # Calculate minutes and seconds
    minutes = seconds // 60
    remaining_seconds = seconds % 60

    # Format the result as mm:ss
    result = "{:02d}:{:02d}".format(minutes, remaining_seconds)

    return result


if __name__ == "__main__":
    app.run(debug=True)