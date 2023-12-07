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
    "user-library-read",  # Add this line
]



@app.route("/")
def index():
    return render_template("index.html")

def get_songs_from_database(run_length_in_minutes, genres, intensity, liked_songs):
    run_length_ms = run_length_in_minutes * 60000

    # Define energy thresholds based on intensity
    energy_thresholds = {
        "high": (0.9, 0.7),
        "medium": (0.7, 0.5),
        "low": (0.5, 0.3)
    }
    energy_upper_threshold, energy_lower_threshold = energy_thresholds.get(intensity, (0.7, 0.5))

    # Query the database for songs that match user's liked songs and other criteria
    response = (
        supabase.table("spotify_database")
        .select("track_id, duration_ms", "track_name", "artists")
        .in_("track_genre", genres)
        .gte("energy", energy_lower_threshold)
        .lte("energy", energy_upper_threshold)
        .order("popularity", desc=True)
        .limit(300)
        .execute()
    )

    data = response.data

    # Prioritize liked songs in the selection
    prioritized_songs = [song for song in data if song['track_id'] in liked_songs]
    other_songs = [song for song in data if song['track_id'] not in liked_songs]

    # Combine liked songs with additional songs, prioritizing liked ones
    combined_songs = prioritized_songs + other_songs

    # Select songs up to the desired run length
    selected, total_duration = [], 0
    for song in combined_songs:
        if total_duration + song["duration_ms"] <= run_length_ms:
            selected.append(song)
            total_duration += song["duration_ms"]
        elif total_duration < run_length_ms:
            selected.append(song)  # Add the last song even if it exceeds the limit
            break

    return selected, total_duration


@app.route("/fetch_songs", methods=["POST"])
def fetch_songs():
    # Store form data in the session for later use
    session['run_length'] = float(request.form.get("run_length"))
    session['genres'] = string_to_list(request.form.get("selectedGenres"))
    session['intensity'] = request.form.get("intensity")
    session['new_playlist_headers'] = {
        'name': bleach.clean(request.form.get("name")),
        'description': bleach.clean(request.form.get("description"))
    }

    if not session['genres'][0]:  # No genre selected
        flash("Please select at least one genre")
        return redirect(url_for('index', _external=True))
    
    # Redirect to Spotify authentication
    return redirect(url_for('generate', _external=True))



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
    code = request.args.get("code")
    if not code:
        flash("No authorization code provided by Spotify.")
        return redirect(url_for('index', _external=True))

    token_info = sp_oauth.get_access_token(code)
    if not token_info:
        flash("Failed to retrieve access token from Spotify.")
        return redirect(url_for('index', _external=True))

    session["token info"] = token_info
    return redirect(url_for("create_playlist", _external=True))


@app.route("/create_playlist")
def create_playlist():
    # INITIALISE THE PLAYLIST
    token_info = session.get("token info", None)
    if not token_info:
        flash("Spotify authentication data not found.")
        return redirect(url_for('index', _external=True))

    sp = Spotify(auth=token_info["access_token"])
    user_info = sp.me()
    user_id = user_info["id"]

    # Fetch user's liked songs
    liked_songs = get_user_liked_songs(sp)
    if not liked_songs:
        flash("Could not fetch liked songs from Spotify.")
        return redirect(url_for('index', _external=True))

    # Retrieve necessary data for the playlist
    run_length = session.get('run_length')
    genres = session.get('genres')
    intensity = session.get('intensity')

    # Get songs from the database
    song_data, _ = get_songs_from_database(run_length, genres, intensity, liked_songs)

    # Extract track IDs
    ids_to_add = [song['track_id'] for song in song_data]

    try:
        # Create the Spotify playlist
        playlist = sp.user_playlist_create(
            user_id,
            name=session['new_playlist_headers']['name'],
            description=session['new_playlist_headers']['description']
        )
        playlist_id = playlist['id']
        session['playlist_url'] = 'https://open.spotify.com/playlist/' + playlist_id
        print("Playlist created:", playlist)  # Log this for debugging

        # Add items to the playlist
        if ids_to_add:
            sp.playlist_add_items(playlist_id, ids_to_add)
    except Exception as e:
        print("Error in playlist creation:", e)  # Log this for debugging
        flash("Error occurred while creating the playlist.")
        return redirect(url_for('index', _external=True))

    return redirect(url_for("export", _external=True))



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

def get_spotify_session():
    token_info = session.get("token info")
    if not token_info or 'access_token' not in token_info:
        # Log for debugging
        print("No token info available in session.")
        return None
    return Spotify(auth=token_info["access_token"])

def get_user_liked_songs(sp):
    sp = get_spotify_session()
    if sp is None:
        print("Spotify session could not be created.")
        return None
    liked_songs = []

    try:
        results = sp.current_user_saved_tracks(limit=50)  # Fetch up to 50 items per call
        while results:
            liked_songs.extend([item['track']['id'] for item in results['items']])
            results = sp.next(results) if results['next'] else None
    except Exception as e:
        print(f"Error fetching user's liked songs: {e}")

    return liked_songs

"""
def get_user_liked_songs():
    sp = get_spotify_session()
    if sp is None:
        print("Spotify session could not be created.")
        return None
    liked_songs = []

    try:
        results = sp.current_user_saved_tracks(limit=50) 
        while results:
            # Log the current batch of results
            print(f"Received {len(results['items'])} liked songs in this batch.")
            liked_songs.extend([item['track']['id'] for item in results['items']])
            results = sp.next(results) if results['next'] else None

        # Log the total number of liked songs retrieved
        print(f"Total liked songs retrieved: {len(liked_songs)}")

    except Exception as e:
        print(f"Error fetching user's liked songs: {e}")

    return liked_songs

"""


if __name__ == "__main__":
    app.run(debug=True)