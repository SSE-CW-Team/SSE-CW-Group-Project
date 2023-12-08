import spotipy
from spotipy.oauth2 import SpotifyOAuth
import csv
import time
import os
import random

# Spotify API Authentication

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='CLIENT_ID',
                                               client_secret='CLIENT_SECRET_KEY',
                                               redirect_uri='CLIENT_REDIRECT_URL',
                                               scope='playlist-read-private'))

# Example pools of genres, artists, and tracks
all_genres = ['acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient', 'anime', 'black-metal', 'bluegrass', 'blues', 'bossanova', 'brazil', 'breakbeat', 'british', 'cantopop', 'chicago-house', 'children', 'chill', 'classical', 'club', 'comedy', 'country', 'dance', 'dancehall', 'death-metal', 'deep-house', 'detroit-techno', 'disco', 'disney', 'drum-and-bass', 'dub', 'dubstep', 'edm', 'electro', 'electronic', 'emo', 'folk', 'forro', 'french', 'funk', 'garage', 'german', 'gospel', 'goth', 'grindcore', 'groove', 'grunge', 'guitar', 'happy', 'hard-rock', 'hardcore', 'hardstyle', 'heavy-metal', 'hip-hop', 'holidays', 'honky-tonk', 'house', 'idm', 'indian', 'indie', 'indie-pop', 'industrial', 'iranian', 'j-dance', 'j-idol', 'j-pop', 'j-rock', 'jazz', 'k-pop', 'kids', 'latin', 'latino', 'malay', 'mandopop', 'metal', 'metal-misc', 'metalcore', 'minimal-techno', 'movies', 'mpb', 'new-age', 'new-release', 'opera', 'pagode', 'party', 'philippines-opm', 'piano', 'pop', 'pop-film', 'post-dubstep', 'power-pop', 'progressive-house', 'psych-rock', 'punk', 'punk-rock', 'r-n-b', 'rainy-day', 'reggae', 'reggaeton', 'road-trip', 'rock', 'rock-n-roll', 'rockabilly', 'romance', 'sad', 'salsa', 'samba', 'sertanejo', 'show-tunes', 'singer-songwriter', 'ska', 'sleep', 'songwriter', 'soul', 'soundtracks', 'spanish', 'study', 'summer', 'swedish', 'synth-pop', 'tango', 'techno', 'trance', 'trip-hop', 'turkish', 'work-out', 'world-music']

def get_spotify_genre_seeds():
    try:
        return sp.recommendation_genre_seeds()['genres']
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Function to randomly select seeds
def get_random_seeds(num_genres=2, num_artists=2, num_tracks=2):
    selected_genres = random.sample(all_genres, num_genres)
    return selected_genres

def get_spotify_id_from_url(url):
    # Extract the ID from a Spotify URL
    parts = url.split('/')
    if len(parts) > 3:
        return parts[4].split('?')[0]  # Extract the ID part
    return None

def fetch_featured_playlists(limit):
    return sp.featured_playlists(limit=limit)['playlists']['items']

def fetch_recommended_tracks(seed_genres=None, seed_artists=None, seed_tracks=None, limit=100):
    if seed_genres is None:
        seed_genres = []
    if seed_artists is None:
        seed_artists = []
    if seed_tracks is None:
        seed_tracks = []

    if not seed_genres and not seed_artists and not seed_tracks:
        raise ValueError("At least one seed genre, artist, or track must be provided")

    return sp.recommendations(seed_genres=seed_genres, seed_artists=seed_artists, seed_tracks=seed_tracks, limit=limit)['tracks']

def is_new_playlist(playlist_url, file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        existing_urls = [line.strip() for line in file]
    return playlist_url not in existing_urls

def append_new_playlists(file_path, log_path, limit1=40, limit2=100, seed_genres=None, seed_artists=None, seed_tracks=None):
    # Fetch and append featured playlists
    new_featured_playlists = fetch_featured_playlists(limit1)
    with open(file_path, 'a') as file:
        for playlist in new_featured_playlists:
            full_url = playlist['external_urls']['spotify']
            if not is_processed(log_path, full_url):
                print(f"Appending new featured playlist URL: {full_url}")
                file.write(full_url + '\n')

    # Fetch and append recommended tracks
    try:
        new_recommended_tracks = fetch_recommended_tracks(seed_genres=seed_genres, seed_artists=seed_artists, seed_tracks=seed_tracks, limit=limit2)
        with open(file_path, 'a') as file:
            for track in new_recommended_tracks:
                full_url = track['external_urls']['spotify']
                if not is_processed(log_path, full_url):
                    print(f"Appending new recommended track URL: {full_url}")
                    file.write(full_url + '\n')
    except ValueError as e:
        print(f"Error fetching recommended tracks: {e}")


# Function to get audio features for multiple tracks
def get_audio_features_for_multiple_tracks(track_uris):
    all_audio_features = []
    for i in range(0, len(track_uris), 100):  # Processing 100 tracks at a time
        batch = track_uris[i:i + 100]
        try:
            audio_features = sp.audio_features(batch)
            all_audio_features.extend(audio_features)
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get('Retry-After', 1))
                time.sleep(retry_after)
            else:
                raise
    return all_audio_features

def remove_duplicates(csv_filename):
    with open(csv_filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        unique_rows = set()

        for row in reader:
            unique_rows.add(tuple(row))  # Add each row as a tuple to the set

    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in unique_rows:
            writer.writerow(row)

    print(f"Duplicates removed from {csv_filename}")

def read_log(log_filename):
    try:
        with open(log_filename, 'r') as file:
            data = file.read().strip()
            if data:
                parts = data.split(',')
                if len(parts) == 2:
                    last_processed_playlist, last_track_index = parts
                    return last_processed_playlist, int(last_track_index)
            return None, -1  # Handle empty file or file with only one part
    except FileNotFoundError:
        return None, -1  # No log file or empty log file
    except ValueError:
        # Handle cases where conversion to int fails
        return None, -1

def add_to_log(log_filename, full_url):
    with open(log_filename, 'a') as file:
        file.write(full_url + '\n')

def is_processed(log_filename, full_url):
    try:
        with open(log_filename, 'r') as file:
            processed_urls = [line.strip() for line in file]
        return full_url in processed_urls
    except FileNotFoundError:
        return False

# Function to check if a track is in the CSV
def is_track_in_csv(track_id, csv_filename):
    try:
        with open(csv_filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if track_id in row:
                    return True
        return False
    except FileNotFoundError:
        return False

# Main program
log_filename = 'playlist_processing_log.txt'
cooldown_period = 60  # Cooldown period in seconds

# genre_seeds = get_spotify_genre_seeds()
# formatted_genre_seeds = [f"'{genre}'" for genre in genre_seeds]
# print(", ".join(formatted_genre_seeds))

seed_genres = get_random_seeds()
seed_artists = []  # Define seed artists if available
seed_tracks = []  # Define seed tracks if available

try:
    # Read the log file to get a list of processed playlist URIs
    processed_playlist_uris = []
    if os.path.exists(log_filename):
        with open(log_filename, 'r') as log_file:
            processed_playlist_uris = [line.strip() for line in log_file]

    # append_new_playlists('spotify_playlist_urls.txt', log_filename, limit1=40, limit2=100, seed_genres=seed_genres,
    #                      seed_artists=seed_artists, seed_tracks=seed_tracks)

    with open('spotify_song_metadata.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write header to CSV if file is empty
        if file.tell() == 0:
            writer.writerow([
                'Track ID', 'Artists', 'Album Name', 'Track Name', 'Popularity',
                'Duration (ms)', 'Explicit', 'Danceability', 'Energy', 'Key',
                'Loudness', 'Mode', 'Speechiness', 'Acousticness', 'Instrumentalness',
                'Liveness', 'Valence', 'Tempo', 'Time Signature', 'Track Genre'
            ])

        last_processed_playlist, last_track_index = read_log(log_filename)

        with open('spotify_playlist_urls.txt', 'r') as playlist_urls_file:
            playlist_urls = [line.strip() for line in playlist_urls_file]
            unprocessed_urls = [url for url in playlist_urls if not is_processed(log_filename, url)]

        # Write back only unprocessed URLs to the file
        with open('spotify_playlist_urls.txt', 'w') as playlist_urls_file:
            for url in unprocessed_urls:
                playlist_urls_file.write(url + '\n')

        # Process each URL
        for url in unprocessed_urls:
            print(f"Processing URL: {url}")
            spotify_id = get_spotify_id_from_url(url)
            print(f"{spotify_id}")
            full_url = 'https://open.spotify.com/' + (
                'track/' if 'track' in url else 'playlist/') + get_spotify_id_from_url(url)
            if not is_processed(log_filename, full_url):
                if 'track' in url:
                    # Process track URL
                    print("Processing track URL...")
                    try:
                        print("Getting track data...")
                        try:
                            track_data = sp.track(spotify_id)  # Fetch track details
                            print(f"Track Data: {track_data}")
                        except spotipy.exceptions.SpotifyException as e:
                            print(f"Error fetching track details: {e}")
                        # Extract relevant track data
                        track_id = track_data['id']
                        track_name = track_data['name']
                        album_name = track_data['album']['name']
                        artists = ', '.join([artist['name'] for artist in track_data['artists']])
                        popularity = track_data['popularity']
                        duration_ms = track_data['duration_ms']
                        explicit = track_data['explicit']

                        # Fetch audio features
                        audio_features = sp.audio_features(track_id)[0]
                        if audio_features:
                            danceability = audio_features['danceability']
                            energy = audio_features['energy']
                            key = audio_features['key']
                            loudness = audio_features['loudness']
                            mode = audio_features['mode']
                            speechiness = audio_features['speechiness']
                            acousticness = audio_features['acousticness']
                            instrumentalness = audio_features['instrumentalness']
                            liveness = audio_features['liveness']
                            valence = audio_features['valence']
                            tempo = audio_features['tempo']
                            time_signature = audio_features['time_signature']

                            # Write to CSV
                            writer.writerow([
                                track_id, artists, album_name, track_name, popularity,
                                duration_ms, explicit, danceability, energy, key,
                                loudness, mode, speechiness, acousticness, instrumentalness,
                                liveness, valence, tempo, time_signature
                            ])
                            print(f"Track {track_name} processed and written to CSV.")
                            add_to_log(log_filename, full_url)
                        else:
                            print(f"No audio features found for track: {track_name}")
                    except spotipy.exceptions.SpotifyException as e:
                        print(f"Error processing track URL {url}: {e}")
                elif 'playlist' in url:
                    # Process playlist URL
                    print("Processing playlist URL...")
                    try:
                        playlist_tracks = sp.playlist_tracks(spotify_id)["items"]
                        for i, track in enumerate(playlist_tracks):
                            track = track['track']
                            if track and not is_track_in_csv(track['id'], 'spotify_song_metadata.csv'):
                                # Extract relevant track data
                                track_id = track['id']
                                track_name = track['name']
                                album_name = track['album']['name']
                                artists = ', '.join([artist['name'] for artist in track['artists']])
                                popularity = track['popularity']
                                duration_ms = track['duration_ms']
                                explicit = track['explicit']

                                # Fetch audio features
                                audio_features = sp.audio_features(track_id)[0]
                                if audio_features:
                                    danceability = audio_features['danceability']
                                    energy = audio_features['energy']
                                    key = audio_features['key']
                                    loudness = audio_features['loudness']
                                    mode = audio_features['mode']
                                    speechiness = audio_features['speechiness']
                                    acousticness = audio_features['acousticness']
                                    instrumentalness = audio_features['instrumentalness']
                                    liveness = audio_features['liveness']
                                    valence = audio_features['valence']
                                    tempo = audio_features['tempo']
                                    time_signature = audio_features['time_signature']

                                    # Write to CSV
                                    writer.writerow([
                                        track_id, artists, album_name, track_name, popularity,
                                        duration_ms, explicit, danceability, energy, key,
                                        loudness, mode, speechiness, acousticness, instrumentalness,
                                        liveness, valence, tempo, time_signature
                                    ])
                                    print(f"Track {track_name} processed and written to CSV.")
                                    add_to_log(log_filename, full_url)
                                else:
                                    print(f"No audio features found for track: {track_name}")

                        # Update the log after processing each playlist
                        add_to_log(log_filename, full_url)

                    except spotipy.exceptions.SpotifyException as e:
                        print(f"Error processing playlist URL {url}: {e}")

            # Cooldown period after processing each URL
            print(f"Cooldown for {cooldown_period} seconds before processing next URL")
            time.sleep(cooldown_period)

        print(f"Songs successfully written to csv from 'spotify_song_metadata.csv'")
        remove_duplicates('spotify_song_metadata.csv')
        remove_duplicates('playlist_processing_log.txt')

except Exception as e:
    print(f"An error occurred: {e}")

