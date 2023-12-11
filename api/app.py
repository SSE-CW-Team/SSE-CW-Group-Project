from flask import Flask, render_template, request, redirect, url_for, session, flash
from spotipy.oauth2 import SpotifyOAuth  # type: ignore
from spotipy import Spotify  # type: ignore
from supabase import create_client, Client  # type: ignore
from dotenv import load_dotenv  # type: ignore
from datetime import timedelta
import bleach  # type: ignore
import os
from cachelib import SimpleCache
from random import shuffle

load_dotenv()

# APP CONFIGURATION #

app = Flask(__name__)

cache = SimpleCache()

# Set lifetime of session, to prevent session hijacking
app.permanent_session_lifetime = timedelta(minutes=10)

# The client information we send to Spotify so they can give us an access token
client_id = os.environ["CLIENT_ID"]
client_secret = os.environ["CLIENT_SECRET"]

# Needed for creating Flask session
app.secret_key = os.environ["SECRET_KEY"]

# Initialize the Supabase client with project URL and public API key
supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_ANON_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

scopes = [  # The amount of access to the account that Spotify will allow us
    "playlist-modify-public",  # create playlist
    "playlist-modify-private",  # create playlist
    "user-library-read",  # fetch user's liked songs
]


# APP ROUTES #

# The home page.
# This contains forms for the user to input details about the playlist they want
@app.route("/")
def index():
    return render_template("index.html")

# FUNCTIONS FOR SELECTING SONGS


# The formula for choosing which songs to prioritise.
# A song's priority is a function of the difference between the input values
# and the actual song values for each slider characteristic. A song is also
# prioritised further if it has been liked by the user.
def sorting_formula(element, slider_values):
    pop_diff = abs(slider_values["popularity"] - float(element["popularity"])) / 100
    tempo_diff = 3 * abs(slider_values["tempo"] - float(element["tempo"])) / 170
    energy_diff = abs(slider_values["energy"] - float(element["energy"]))
    dance_diff = abs(slider_values["danceability"] - float(element["danceability"]))
    priority = 6 - (pop_diff + tempo_diff + energy_diff + dance_diff)
    if element["liked"] is True:
        priority *= 1.4
    return priority


# Function to retrieve the right number of songs from the database, according to the
# requested length of the playlist. Returns a list of songs, the playlist's total
# duration and the data needed to make the graph on the 'export' page.
def get_songs_from_database(
    run_length_in_minutes, genres, slider_values, bool_flags, liked_songs=[]
):
    # Conversion needed since duration data is stored in the database in ms
    run_length_ms = run_length_in_minutes * 60000
    # Query to supabase
    query = (
        supabase.table("spotify_database")
        .select(
            "track_id",
            "duration_ms",
            "track_name",
            "artists",
            "popularity",
            "tempo",
            "energy",
            "danceability",
        )
        .in_("track_genre", genres)
    )
    # Eliminate songs which fail checkbox criteria
    if not bool_flags["allowExplicit"]:
        query = query.eq("explicit", False)

    if bool_flags["instrumentalOnly"]:
        query = query.gte("instrumentalness", 0.5)

    if not bool_flags["includeAcoustic"]:
        query = query.lte("acousticness", 0.5)

    if not bool_flags["includeLive"]:
        query = query.lte("liveness", 0.5)

    response = query.execute()
    data = response.data

    for song in data:
        # 'True' will give the song a song a higher priority in the sorting algorithm
        song['liked'] = song['track_id'] in liked_songs
    data = sorted(data, key=lambda song: sorting_formula(song, slider_values), reverse=True)

    selected = []
    total_duration = 0

    for i in range(len(data)):
        song = data[i]
        # Eliminate duplicates
        if i != 0 and song["track_name"] == data[i - 1]["track_name"]:
            continue
        if total_duration + song["duration_ms"] <= run_length_ms:
            selected.append(song)
            total_duration += song["duration_ms"]
        else:
            selected.append(song)
            total_duration += song["duration_ms"]
            break
    shuffle(selected)

    # Generate data for graph:
    graph_data = []
    current_time = 0
    for song in selected:
        song_length = (int(song["duration_ms"]) / 1000) / 60
        graph_data.append({"name": song["track_name"], "time": current_time})
        current_time += song_length

    return selected, total_duration, graph_data


# Function which sends Spotify our details and receives a response
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for("_redirect", _external=True),
        scope=scopes,
    )


# Function to set up Spotify client
def get_spotify_session():
    token_info = session.get("token info")
    if not token_info or "access_token" not in token_info:
        # Log for debugging
        print("No token info available in session.")
        return None
    return Spotify(auth=token_info["access_token"])


# Route for fetching liked songs
@app.route("/fetch_liked_songs")
def fetch_liked_songs():
    sp = get_spotify_session()
    if sp is None:
        return "Spotify session could not be created."
    # Liked songs are cached for a limited time so the user doesn't have to wait
    # for the liked song data to be retrieved multiple times
    liked_songs = cache.get("liked_songs")
    if liked_songs is None:
        liked_songs = []
        try:
            results = sp.current_user_saved_tracks(
                limit=50
            )  # Fetch up to 50 items per call
            while results:
                liked_songs.extend([item["track"]["id"] for item in results["items"]])
                results = sp.next(results) if results["next"] else None
            cache.set("liked_songs", liked_songs, timeout=900)  # Saved for 15 minutes
        except Exception:
            return "Error fetching user's liked songs"

    requested_data = get_songs_from_database(
        session["run_length"],
        session["genres"],
        session["slider_values"],
        session["bool_flags"],
        liked_songs,
    )

    song_data = requested_data[0]
    session["graph_data"] = requested_data[2]
    session["track_ids"] = [i["track_id"] for i in song_data]
    session["titles"] = [i["track_name"] for i in song_data]
    session["artists"] = [i["artists"].replace(";", ", ") for i in song_data]
    session["lengths"] = [
        seconds_to_mm_ss(int(i["duration_ms"] / 1000)) for i in song_data
    ]
    return redirect(url_for("export", _external=True))


# App route where songs are fetched
@app.route("/fetch_songs", methods=["POST"])
def fetch_songs():
    run_length = float(request.form.get("run_length"))
    genres = string_to_list(request.form.get("selectedGenres"))

    if not genres[0]:  # No genre selected
        flash("Please select at least one genre")
        return redirect(url_for("index", _external=True))

    # Dictionary for slider values and thresholds
    slider_values = {
        "energy": float(request.form.get("energyValue")),
        "popularity": float(request.form.get("popularityValue")),
        "danceability": float(request.form.get("danceabilityValue")),
        "tempo": float(request.form.get("tempoValue")),
    }

    session["workout"] = request.form.get("workout")

    # Dictionary for boolean flags
    bool_flags = {
        "allowExplicit": request.form.get("allowExplicit") == "on",
        "instrumentalOnly": request.form.get("instrumentalOnly") == "on",
        "includeAcoustic": request.form.get("includeAcoustic") == "on",
        "includeLive": request.form.get("includeLive") == "on",
        "includeLikedSongs": request.form.get("includeLikedSongs") == "on",
    }

    print(bool_flags)

    session["includeLikedSongs"] = bool_flags["includeLikedSongs"]
    session["slider_values"] = slider_values
    session["run_length"] = run_length
    session["bool_flags"] = bool_flags
    session["genres"] = genres

    if session["includeLikedSongs"]:
        # Get user to log in so liked songs can be retrieved
        sp_oauth = get_spotify_oauth()
        authorise_url = sp_oauth.get_authorize_url()
        return redirect(authorise_url)

    else:
        requested_data = get_songs_from_database(
            run_length, genres, slider_values, bool_flags
        )
        song_data = requested_data[0]
        session["graph_data"] = requested_data[2]
        session["track_ids"] = [i["track_id"] for i in song_data]
        session["titles"] = [i["track_name"] for i in song_data]
        session["artists"] = [i["artists"].replace(";", ", ") for i in song_data]
        session["lengths"] = [
            seconds_to_mm_ss(int(i["duration_ms"] / 1000)) for i in song_data
        ]
        return redirect(url_for("export", _external=True))


# App route where created playlist data is displayed
@app.route("/export")
def export():
    exported = False
    if session.get("exported", False) is True:
        exported = True
        session.pop("exported")
    return render_template(
        "export.html",
        graph_data=session["graph_data"],
        workout=session["workout"],
        exported=exported,
    )


# App route to which user is sent when they click "Export to Spotify"
@app.route("/generate", methods=["POST", "GET"])
def generate():
    name = bleach.clean(request.form.get("name"))
    description = bleach.clean(request.form.get("description"))
    session["new_playlist_headers"] = {}
    session["new_playlist_headers"]["name"] = name
    session["new_playlist_headers"]["description"] = description
    session.permanent = True
    sp_oauth = get_spotify_oauth()
    authorise_url = sp_oauth.get_authorize_url()
    return redirect(authorise_url)


# App route which Spotify redirects the user to after login
@app.route("/redirect")
def _redirect():
    sp_oauth = get_spotify_oauth()
    try:
        session.pop("token info")
    except KeyError:
        pass
    code = request.args.get("code", None)  # returns None if request fails
    token_info = sp_oauth.get_access_token(code)
    session["token info"] = token_info
    if session["includeLikedSongs"]:
        session["includeLikedSongs"] = None
        return redirect(url_for("fetch_liked_songs", _external=True))
    else:
        return redirect(url_for("create_playlist", _external=True))


# App route for playlist creation
@app.route("/create_playlist")
def create_playlist():
    # INITIALISE THE PLAYLIST
    # It's good practice to create a new client each time
    sp = get_spotify_session()
    user_info = sp.me()
    user_id = user_info["id"]
    try:
        sp.user_playlist_create(
            user_id,
            name=session["new_playlist_headers"]["name"],
            description=session["new_playlist_headers"]["description"],
        )
    except Exception as e:
        return "Error creating playlist: " + str(e)
    # Check that this is the right playlist
    last_playlist_id = sp.user_playlists(user_id)["items"][0]["id"]
    session["playlist_url"] = "https://open.spotify.com/playlist/" + last_playlist_id
    # ADD ITEMS TO PLAYLIST
    ids_to_add = session.get("track_ids")
    try:
        sp.playlist_add_items(last_playlist_id, ids_to_add)
    except Exception:
        return "Error adding songs to playlist"
    session["exported"] = True
    return redirect(url_for("export", _external=True))


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
