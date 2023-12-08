import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='CLIENT_ID',
                                               client_secret='CLIENT_SECRET_KEY',
                                               redirect_uri='CLIENT_REDIRECT_URL',
                                               scope='playlist-read-private'))


all_genres = ['acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient', 'anime', 'black-metal', 'bluegrass', 'blues', 'bossanova', 'brazil', 'breakbeat', 'british', 'cantopop', 'chicago-house', 'children', 'chill', 'classical', 'club', 'comedy', 'country', 'dance', 'dancehall', 'death-metal', 'deep-house', 'detroit-techno', 'disco', 'disney', 'drum-and-bass', 'dub', 'dubstep', 'edm', 'electro', 'electronic', 'emo', 'folk', 'forro', 'french', 'funk', 'garage', 'german', 'gospel', 'goth', 'grindcore', 'groove', 'grunge', 'guitar', 'happy', 'hard-rock', 'hardcore', 'hardstyle', 'heavy-metal', 'hip-hop', 'holidays', 'honky-tonk', 'house', 'idm', 'indian', 'indie', 'indie-pop', 'industrial', 'iranian', 'j-dance', 'j-idol', 'j-pop', 'j-rock', 'jazz', 'k-pop', 'kids', 'latin', 'latino', 'malay', 'mandopop', 'metal', 'metal-misc', 'metalcore', 'minimal-techno', 'movies', 'mpb', 'new-age', 'new-release', 'opera', 'pagode', 'party', 'philippines-opm', 'piano', 'pop', 'pop-film', 'post-dubstep', 'power-pop', 'progressive-house', 'psych-rock', 'punk', 'punk-rock', 'r-n-b', 'rainy-day', 'reggae', 'reggaeton', 'road-trip', 'rock', 'rock-n-roll', 'rockabilly', 'romance', 'sad', 'salsa', 'samba', 'sertanejo', 'show-tunes', 'singer-songwriter', 'ska', 'sleep', 'songwriter', 'soul', 'soundtracks', 'spanish', 'study', 'summer', 'swedish', 'synth-pop', 'tango', 'techno', 'trance', 'trip-hop', 'turkish', 'work-out', 'world-music']

def get_random_seeds(num_genres=2, num_artists=2, num_tracks=2):
    selected_genres = random.sample(all_genres, num_genres)
    return selected_genres

# Function to create a playlist
def create_playlist():
    # Create a new playlist
    playlist_name = 'Recommended Playlist'
    playlist_description = 'A playlist of recommended tracks'
    user_id = sp.me()['id']  # Get the user's Spotify ID

    playlist = sp.user_playlist_create(user_id, playlist_name, public=True, description=playlist_description)
    playlist_id = playlist['id']

    seed_genres = get_random_seeds()
    seed_artists = []  # Define seed artists if available
    seed_tracks = []  # Define seed tracks if available

    # Get recommended tracks based on seeds
    recommended_tracks = sp.recommendations(seed_artists=seed_artists,
                                            seed_genres=seed_genres,
                                            seed_tracks=seed_tracks,
                                            limit=100)

    # Add recommended tracks to the playlist
    track_ids = [track['id'] for track in recommended_tracks['tracks']]
    sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)

    # Write the playlist URL to the file
    playlist_url = f'https://open.spotify.com/playlist/{playlist_id}'
    with open('spotify_playlist_urls.txt', 'a') as urls_file:
        urls_file.write(playlist_url + '\n')

    return playlist_id


def read_playlist_urls(filename):
    playlist_urls = []
    with open(filename, 'r') as file:
        playlist_urls = file.readlines()
    return playlist_urls

# Function to delete a playlist and remove its URL from the file
# Function to delete a playlist and remove its URL from the file
def delete_playlist(playlist_id, filename):
    user_id = sp.me()['id']  # Get the user's Spotify ID
    try:
        sp.user_playlist_unfollow(user_id, playlist_id)
        print(f"Playlist {playlist_id} deleted successfully")
        # Remove the URL from the file
        with open(filename, 'r') as file:
            lines = file.readlines()
        with open(filename, 'w') as file:
            for line in lines:
                if line.strip() != f'https://open.spotify.com/playlist/{playlist_id}':
                    file.write(line)
    except Exception as e:
        print(f"Error deleting playlist {playlist_id}: {str(e)}")


# Repeat the playlist creation and deletion process
for i in range(2):
    try:
        playlist_id = create_playlist()
        print(f"Playlist {i + 1} created successfully")
    except Exception as e:
        print(f"Error creating or deleting playlist {i + 1}: {str(e)}")

    time.sleep(60)  # Delay for 5 seconds before creating the next playlist

playlist_urls_to_delete = read_playlist_urls('playlist_processing_log.txt')

# Delete the playlists and remove URLs
for url in playlist_urls_to_delete:
    # Extract playlist_id from the URL
    parts = url.split('/')
    if len(parts) > 3:
        playlist_id_to_delete = parts[4]
        delete_playlist(playlist_id_to_delete, 'playlist_processing_log.txt')
        time.sleep(5)  # Delay for 5 seconds before creating the next playlist

# Clear the playlist_processing_log.txt file after processing
open('playlist_processing_log.txt', 'w').close()