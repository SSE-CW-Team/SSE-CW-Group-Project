from flask import Flask, render_template, request, redirect, url_for, session, flash
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
    # Construct query
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
        )
        .in_("track_genre", genres)
    )

    # # Add conditions based on boolean flags
    # if not bool_flags["allowExplicit"]:
    #     query = query.eq("explicit", False)

    # if bool_flags["instrumentalOnly"]:  # Adjust thresholds as appropriate
    #     query = query.gte("instrumentalness", 0.5)

    # if bool_flags["includeAcoustic"]:
    #     query = query.gte("acousticness", 0.5)

    # if bool_flags["includeLive"]:
    #     query = query.gte("liveness", 0.5)
    # print("Query is",query)
    # Execute query
    response = query.execute()

    data = response.data

    # Process data
    data = response.data
    print("Slider value:", slider_values)

    def sorting_formula(element):
        pop_diff = abs(slider_values["popularity"] - float(element["popularity"])) / 100
        tempo_diff = abs(slider_values["tempo"] - float(element["tempo"])) / 140
        energy_diff = abs(slider_values["energy"] - float(element["energy"]))
        priority = pop_diff + tempo_diff + energy_diff
        return priority

    data = sorted(data, key=sorting_formula)

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
    name = bleach.clean(request.form.get("name"))
    description = bleach.clean(request.form.get("description"))
    session["new_playlist_headers"] = {}
    session["new_playlist_headers"]["name"] = name
    session["new_playlist_headers"]["description"] = description
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


def seconds_to_mm_ss(seconds):
    # Calculate minutes and seconds
    minutes = seconds // 60
    remaining_seconds = seconds % 60

    # Format the result as mm:ss
    result = "{:02d}:{:02d}".format(minutes, remaining_seconds)

    return result


if __name__ == "__main__":
    app.run(debug=True)
