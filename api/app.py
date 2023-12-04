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


def get_songs_from_database(run_length_in_minutes, genres, intensity):
    # Variables (You can modify these based on user input)
    run_length_ms = run_length_in_minutes * 60000

    # Energy thresholds for the high intensity
    if intensity == "high":
        energy_upper_threshold = 0.9
        energy_lower_threshold = 0.7
    elif intensity == "medium":
        energy_upper_threshold = 0.7
        energy_lower_threshold = 0.5
    elif intensity == "low":
        energy_upper_threshold = 0.5
        energy_lower_threshold = 0.3

    # Query using these inputs
    response = (
        supabase.table("spotify_database")
        .select("track_id, duration_ms", "track_name", "artists")
        .gte("energy", energy_lower_threshold)
        .lte("energy", energy_upper_threshold)
        .in_("track_genre", genres)
        .order("popularity", desc=True)
        .limit(300)
        .execute()
    )

    data = response.data
    selected = []
    total_duration = 0

    for song in data:
        if total_duration + song["duration_ms"] <= run_length_ms:
            selected.append(song)
            total_duration += song["duration_ms"]
        else:
            selected.append(song)
            total_duration += song["duration_ms"]
            break

    return selected, total_duration


@app.route("/fetch_songs", methods=["POST"])
def fetch_songs():
    run_length = float(request.form.get("run_length"))
    genres = string_to_list(request.form.get("selectedGenres"))
    intensity = request.form.get("intensity")
    # Add input data to a global dict
    session['new_playlist_headers'] = {}
    name = request.form.get("name")
    session['new_playlist_headers']['name'] = bleach.clean(name)
    description = request.form.get("description")
    session['new_playlist_headers']["description"] = bleach.clean(description)
    # Get track ids
    song_data = get_songs_from_database(run_length, genres, intensity)[0]
    session["track_ids"] = [i['track_id'] for i in song_data]
    session["titles"] = [i['track_name'] for i in song_data]
    session["artists"] = [i['artists'].replace(';', ', ') for i in song_data]
    if not genres[0]:  # No genre selected
        flash("Please select at least one genre")
        return redirect(url_for('index', _external=True))
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
    ids_to_add = session.get("track_ids")
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


def string_to_list(input_string):
    result_list = input_string.split(", ")
    result_list = [item.strip().lower() for item in result_list]
    return result_list


if __name__ == "__main__":
    app.run(debug=True)
