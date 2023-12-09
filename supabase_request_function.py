# Import necessary libraries
from supabase import create_client, Client
import os

# Initialize the Supabase client with project URL and public API key
supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_ANON_KEY']
supabase: Client = create_client(supabase_url, supabase_key)

# Variables (You can modify these based on user input)
exercise_intensity = 'high'
run_length_in_minutes = 30
favorite_genre = 'rock'
favorite_artist = 'Artist Name'

# Convert run length to milliseconds
run_length_ms = run_length_in_minutes * 60000
max_playlist_duration_ms = run_length_ms * 1.2

# Energy thresholds for the high intensity
energy_upper_threshold = 0.7
energy_lower_threshold = 0.4

# Query using these inputs
data = supabase.table('Spotify: Most streamed songs by genre') \
    .select('*') \
    .gte('energy', energy_lower_threshold) \
    .lte('energy', energy_upper_threshold) \
    .eq('track_genre', favorite_genre) \
    .order('popularity', ascending=False) \
    .limit(200) \
    .execute()

# Handle the data
if data.get('error'):
    print('Error fetching data:', data.get('error'))
else:
    fetched_data = data.get('data', [])
    # Sort by artist preference
    sorted_data = sorted(fetched_data, key=lambda x: (x['artists'] != favorite_artist))


# Function to build the playlist
def build_playlist(tracks, target_duration_ms, max_duration_ms):
    playlist = []
    playlist_duration_ms = 0

    for track in tracks:
        if playlist_duration_ms + track['duration_ms'] <= max_duration_ms:
            playlist.append(track['track_id'])  # Append only the track_id
            playlist_duration_ms += track['duration_ms']
        elif playlist_duration_ms >= target_duration_ms:
            break
        else:
            playlist.append(track['track_id'])  # Append only the track_id
            break

    # Adjust playlist length if necessary
    while playlist_duration_ms > max_duration_ms:
        removed_track_id = playlist.pop()
        removed_track = next((item for item in tracks if item['track_id'] == removed_track_id), None)
        playlist_duration_ms -= removed_track['duration_ms'] if removed_track else 0

    return playlist


# Build the final playlist
final_playlist = build_playlist(sorted_data, run_length_ms, max_playlist_duration_ms)
print('Final playlist track IDs:', final_playlist)
