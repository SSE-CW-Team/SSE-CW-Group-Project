// Initialize the Supabase client with project URL and public API key
// These are saved as Vercel environmental variables under these names:
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'SUPABASE_URL'
const supabaseKey = 'SUPABASE_ANON_KEY'
const supabase = createClient(supabaseUrl, supabaseKey)

// When user signs in, call signInWithOAuth() with github as the provider:
async function signInWithGithub() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'github',
  })
}

// When user signs in, call signInWithOAuth() with github as the provider:
async function signOut() {
  const { error } = await supabase.auth.signOut()
}


/** SQL query template **/

// Receive inputs from user
const exerciseIntensity = 'high'; // Could map to a range of 'energy' values
const runLengthInMinutes = 30;    // Run length
const favoriteGenre = 'rock';     // Should map to 'track_genre'
const favoriteArtist = 'Artist Name'; // User's favorite artist

// Convert run length to milliseconds since 'duration_ms' is in milliseconds
const runLengthMs = runLengthInMinutes * 60000;
const maxPlaylistDurationMs = runLengthMs * 1.2; // Maximum allowed duration of the playlist

// Build ranges/logic for selection
// Example: map the intensity to a range or specific value of 'energy'
const energyUpperThreshold = 0.7; // High intensity
const energyLowerThreshold = 0.4; // Adjust for a range

// Query using these inputs
let { data, error } = await supabase
  .from('Spotify: Most streamed songs by genre') // Adjust the table name as needed
  .select('*')
  .gte('energy', energyLowerThreshold) // Greater than or equal to lower threshold for 'high' intensity
  .lte('energy', energyUpperThreshold) // Less than or equal to upper threshold for 'high' intensity
  .eq('track_genre', favoriteGenre) // Equal to the favorite genre
  .order('popularity', { ascending: false }) // Order by popularity
  .limit(200); // Fetch a reasonable number of songs to ensure we can build the playlist

// Check for errors and handle the data
if (error) {
  console.error('Error fetching data:', error);
  // Handle the error accordingly
} else if (data) {
  // Sort by artist preference
  let sortedData = data.sort((a, b) => {
    if (a.artists === favoriteArtist) return -1;
    if (b.artists === favoriteArtist) return 1;
    return 0;
  });

  // Function to build the playlist
  const buildPlaylist = (sortedData, targetDurationMs, maxDurationMs) => {
    let playlist = [];
    let playlistDurationMs = 0;

    for (const track of sortedData) {
      if (playlistDurationMs + track.duration_ms <= maxDurationMs) {
        playlist.push(track);
        playlistDurationMs += track.duration_ms;
      } else {
        // If adding the next song exceeds the max duration, check if we are already within the target duration
        if (playlistDurationMs >= targetDurationMs) {
          break;
        }
        // If not, keep this song and stop adding further songs
        playlist.push(track);
        break;
      }
    }

    // Check if the playlist is too long and remove tracks if necessary
    while (playlistDurationMs > maxDurationMs) {
      const removedTrack = playlist.pop();
      playlistDurationMs -= removedTrack.duration_ms;
    }

    return playlist;	// return as array of song titles or track_IDs for Spotify API
  };

  // Build and adjust the playlist based on the actual song durations
  const finalPlaylist = buildPlaylist(sortedData, runLengthMs, maxPlaylistDurationMs);

  console.log('Final playlist:', finalPlaylist);
  // Process the final playlist as needed
}
