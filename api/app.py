from flask import Flask, render_template, request, redirect, url_for, session
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import time
import os

app = Flask(__name__)

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
app.secret_key = os.environ['SECRET_KEY']

scopes = [  # The amount of access to the account that Spotify allows us
    "playlist-modify-public",
    "playlist-modify-private",
]

songs_to_add = []   # Not sure this should be a global variable


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST', 'GET'])
def generate():
    # data = request.form
    # distance = data.get('distance')
    # location = data.get('location')
    # genre = data.get('genre')
    # intensity = data.get('intensity')
    # In later stages, the logic to generate the playlist and running route
    # would be added in a function. Instead, the program has already picked
    # Oasis - Wonderwall for you and nothing else. Sorry about that.
    # Request Spotify to log the user in
    global new_playlist_name
    # I've made these global since they are used in a different function
    # Perhaps there is a better way of doing this.
    new_playlist_name = "Pace playlist with a song!"
    # Could test for artists that won't be found as well
    songs_to_add.append({"artist": "oasis", "title": "wonderwall"})
    global description
    description = "A new playlist created through Pace app!"
    global collaborative
    collaborative = "false"
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
@app.route('/redirect')
def _redirect():
    sp_oauth = get_spotify_oauth()
    session.clear()
    code = request.args.get('code', None)  # returns None if request fails
    token_info = sp_oauth.get_access_token(code)
    session["token info"] = token_info  # needed for refreshing token
    return redirect(url_for('create_playlist', _external=True))


# The Spotify access token expires after an hour. This function uses
# the refresh token provided by Spotify to make sure that this
# isn't a problem
def get_refreshed_token():
    token_info = session.get("token info", None)  # None if request fails
    timeNow = int(time.time())
    if token_info['expires_at'] - timeNow < 60:  # token expires after an hour
        sp_oauth = get_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info


@app.route('/create_playlist')  # probably doesn't need its own url
def create_playlist():
    # INITIALISE THE PLAYLIST
    print("Refreshing token...")
    token_info = get_refreshed_token()
    print("Creating Spotify client...")
    sp = Spotify(auth=token_info['access_token'])
    print("Getting user info...")
    user_info = sp.me()
    print("Getting user id...")
    user_id = user_info["id"]
    print("Creating playlist...")
    try:
        sp.user_playlist_create(user_id,
                                new_playlist_name,
                                collaborative=collaborative,
                                description=description
                                )
    except Exception as e:
        return "Error creating playlist: " + str(e)
    # Check that this is the right playlist
    last_playlist_id = sp.user_playlists(user_id)["items"][0]["id"]
    # ADD ITEMS TO PLAYLIST
    print("Adding songs to playlist...")
    for i in range(len(songs_to_add)):
        # Get artist and title of song from song list
        search_input = ' '.join(list(songs_to_add[i].values()))
        # Spotify search for artist and title
        search_results = sp.search(search_input)
        # Could make sure artist matches??
        first_result = search_results["tracks"]["items"][0]
        # Get the first result of the search and add to list
        song_id = first_result["id"]
        try:
            sp.playlist_add_items(last_playlist_id, [song_id])
        except Exception:
            continue
    return redirect(url_for('success', _external=True))


def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('_redirect', _external=True),
        scope=scopes
    )


# Page that links you to Spotify. Maybe it could contain a link
# to your playlist instead?
@app.route('/success')
def success():
    return render_template("success_page.html")


if __name__ == '__main__':
    app.run(debug=True)
