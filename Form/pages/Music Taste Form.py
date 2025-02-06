import streamlit as st
import pandas as pd
import requests
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import time
import threading
import os

def _get_session():
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_id

def fetch_artist_data(artist_name, known_list, u_list):
    artist_id = get_artist_id(artist_name)
    top_songs_first_three, top_songs_last_three = get_top_songs_from_ranked_artists(artist_id, limit=15)
    known_list.extend(top_songs_first_three)
    u_list.extend(top_songs_last_three)

def get_artist_id(artist_name):
    """Search for an artist and return their ID."""
    search_url = f"https://api.deezer.com/search/artist?q={artist_name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']  # Return the first artist found
    return None

def get_artist_id_spotify(artist_name):
    results = sp.search(q=artist_name, type='artist', limit=1)
    if results['artists']['items']:
        return results['artists']['items'][0]['id']
    return None

def get_recommendations_d(artist_id, limit):
    """Get recommendations based on the artist ID."""
    recommendations_url = f"https://api.deezer.com/artist/{artist_id}/related?limit={limit}"
    response = requests.get(recommendations_url)
    if response.status_code == 200:
        data = response.json()
        return data['data']  # Return all related artists
    return []

def get_spotify_popularity(spotify_id):
    """Get the Spotify popularity of an artist."""
    artist = sp.artist(spotify_id)
    return artist['popularity']  # Return the popularity score

def get_ranked_artists(artist_id, limit):
    """Get a list of related artists ranked by Spotify popularity."""
    related_artists = get_recommendations_d(artist_id, limit)
    artists_with_popularity = []

    for artist in related_artists:
        spotify_id =get_artist_id_spotify(artist['name'])  # Assuming this is the Spotify ID
        popularity = get_spotify_popularity(spotify_id)
        artists_with_popularity.append({
            'name': artist['name'],
            'popularity': popularity,
            'spotify_id': spotify_id
        })

    # Sort artists by popularity in descending order
    ranked_artists = sorted(artists_with_popularity, key=lambda x: x['popularity'], reverse=True)
    return ranked_artists

def get_top_track(spotify_id):
    """Get the top track of an artist."""
    top_tracks = sp.artist_top_tracks(spotify_id)
    if top_tracks['tracks']:
        return top_tracks['tracks'][0]  # Return the top track
    return None

def get_track_u(spotify_id):
    """Get the top track of an artist."""
    top_tracks = sp.artist_top_tracks(spotify_id)
    if top_tracks['tracks']:
        return top_tracks['tracks'][4]  # Return the top track
    return None

def search_deezer_track(track_name, artist_name):
    """Search for a track on Deezer and return its ID."""
    search_url = f"https://api.deezer.com/search?q={track_name} {artist_name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']  # Return the first track's ID found
    return None

def get_top_songs_from_ranked_artists(artist_id, limit):
    """Get top songs from the first three and last three ranked artists."""
    ranked_artists = get_ranked_artists(artist_id, limit)

    # Get top songs for the first three artists
    top_songs_first_three = []
    for artist in ranked_artists[:3]:
        top_track = get_top_track(artist['spotify_id'])

        if top_track:
            deezer_id = search_deezer_track(top_track['name'], artist['name'])
            top_songs_first_three.append({
                'artist': artist['name'],
                'top_song': top_track['name'],
                'spotify_id': artist['spotify_id'],
                'cover_image': top_track['album']['images'][0]['url'],
                'deezer_id': deezer_id
            })
    # Get top songs for the last three artists
    top_songs_last_three = []
    for artist in ranked_artists[-3:]:
        top_track = get_track_u(artist['spotify_id'])
        if top_track:
            deezer_id = search_deezer_track(top_track['name'], artist['name'])
            top_songs_last_three.append({
                'artist': artist['name'],
                'top_song': top_track['name'],
                'spotify_id': artist['spotify_id'],
                'cover_image': top_track['album']['images'][0]['url'],
                'deezer_id': deezer_id
            })

    return top_songs_first_three, top_songs_last_three

def get_track_preview(deezer_id):
    """Fetch track details from Deezer and return the preview URL."""
    track_url = f"https://api.deezer.com/track/{deezer_id}"
    response = requests.get(track_url)
    print(f"Response: {response}")  # Print the response object

    if response.status_code == 200:
        data = response.json()
        preview_url = data.get('preview')  # Attempt to get the preview URL
        return preview_url  # Return the preview URL
    else:
        print(f"Error: {response.status_code}")  # Print error status if not 200
    return None

## Initialization
load_dotenv()
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

# Initialize Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id,
                                                           client_secret=client_secret))

if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = False
if 'recommendations_shown' not in st.session_state:
    st.session_state.recommendations_shown = False
if 'age' not in st.session_state:
    st.session_state.age = ""
if 'genre_input' not in st.session_state:
    st.session_state.genre_input = ""
if 'artist_input' not in st.session_state:
    st.session_state.artist_input = ""
if 'current_id' not in st.session_state:
    st.session_state.current_id = 1
if 'known_list' not in st.session_state:
    st.session_state.known_list = []
if 'u_list' not in st.session_state:
    st.session_state.u_list = []
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'songs' not in st.session_state:
    st.session_state.songs = False
if 'playlist' not in st.session_state:
    st.session_state.playlist = False
if 'combined_list' not in st.session_state:
    st.session_state.combined_list = []
if 'selected_count' not in st.session_state:
    st.session_state.selected_count = 0
if "sidebar_hidden" not in st.session_state:
    st.session_state.sidebar_hidden = True  # Start with sidebar hidden
if "show_message" not in st.session_state:
    st.session_state.show_message = False

if st.session_state.sidebar_hidden:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

user_session = _get_session()
data_directory = os.path.join("Form", "data", f"{user_session}")
os.makedirs(data_directory, exist_ok=True)
playlist_file_path = os.path.join(data_directory, f"playlist_{user_session}.csv")
# st.set_page_config(page_title="Music Taste Form")
st.title("Music Taste Form")
st.write("Hello! We invite you to take part in a short experiment where you'll answer a few questions about yourself "
         "and your musical tastes. This information will help us create a personalized song list for you. "
         "After that, you'll have the opportunity to listen to the songs and choose three to add to a playlist. "
         "Thank you for your participation!")


# First form for user input
with st.form("my_form"):
    st.write("Please fill all the fields of the form")
    st.session_state.age = st.text_input("Please write your age", value=st.session_state.age)
    st.session_state.genre_input = st.text_input("Can you tell me your three favourite genres (comma-separated)?",
                                                 value=st.session_state.genre_input)
    st.session_state.artist_input = st.text_input("Can you tell me your three favourite artists (comma-separated)?",
                                                  value=st.session_state.artist_input)

    submit = st.form_submit_button('Submit')

# After form submission
if submit:
    if not st.session_state.age or not st.session_state.genre_input or not st.session_state.artist_input:
        st.error("Please fill in all required fields.")
    else:
        try:
            age = int(st.session_state.age)
            if age < 18 or age > 80:
                st.error("Please enter a valid age between 18 and 80")
        except ValueError:
            st.error("Please enter a valid age")

        if ',' not in st.session_state.genre_input or ',' not in st.session_state.artist_input:
            st.error(" Please ensure that genres and artists are separated by comma")
        else:
            st.markdown('**Thank you for answering the form!**', unsafe_allow_html=True)

            # Process the artist and genre input into lists
            artists = [artist.strip() for artist in st.session_state.artist_input.split(',')]
            genres = [genre.strip() for genre in st.session_state.genre_input.split(',')]

            print("Before recommended tracks")
            with st.spinner('In a moment, a list of songs will be displayed...'):
                start_time = time.time()
                threads = []
                known_list = []
                u_list = []

                for artist_name in artists:
                    thread = threading.Thread(target=fetch_artist_data, args=(artist_name, known_list, u_list))
                    threads.append(thread)
                    thread.start()

                for thread in threads:
                    thread.join()

                random.shuffle(known_list)
                random.shuffle(u_list)
                st.session_state.known_list = known_list[:3]
                st.session_state.u_list = u_list[:3]

                # Step 2: Combine the two lists
                combined_list = st.session_state.known_list + st.session_state.u_list

                # Step 3: Ensure uniqueness and maintain a total of 6 songs
                unique_combined_list = []
                seen = set()

                # Add songs from the combined list while ensuring uniqueness
                for song in combined_list:
                    # Use a unique identifier, e.g., song['top_song'] or song['deezer_id']
                    unique_id = song['top_song']  # Change this to the appropriate key for uniqueness
                    if unique_id not in seen:
                        seen.add(unique_id)
                        unique_combined_list.append(song)

                # If we have fewer than 6 unique songs, replace duplicates from the original lists
                while len(unique_combined_list) < 6:
                    # Check which list to pull from for replacements
                    if len(st.session_state.known_list) < 3:
                        # Add from known_list if there are still songs left
                        for song in known_list:
                            unique_id = song['top_song']  # Change this to the appropriate key for uniqueness
                            if unique_id not in seen:
                                unique_combined_list.append(song)
                                seen.add(unique_id)
                                if len(unique_combined_list) == 6:
                                    break
                    if len(unique_combined_list) < 6 and len(st.session_state.u_list) < 3:
                        # Add from u_list if there are still songs left
                        for song in u_list:
                            unique_id = song['top_song']  # Change this to the appropriate key for uniqueness
                            if unique_id not in seen:
                                unique_combined_list.append(song)
                                seen.add(unique_id)
                                if len(unique_combined_list) == 6:
                                    break
                # Step 4: Store the unique combined list in session state
                st.session_state.combined_list = unique_combined_list[:6]

                elapsed_time = time.time() - start_time
                print(f"Elapsed time before displaying known_list and u_list: {elapsed_time:.2f} seconds")
                st.session_state.combined_list = st.session_state.known_list + st.session_state.u_list
                random.shuffle(st.session_state.combined_list)
# Display the recommended tracks
if st.session_state.known_list and st.session_state.u_list:

    st.markdown("Here there is a list of songs that you can listen to. After that you will put the one that you choose in a playlist.")
    cols = st.columns(3)
    for index, track in enumerate(st.session_state.combined_list):
        # Get the current column based on the index
        col = cols[index % 3]

        with col:
            # Display the cover image
            #st.image(track['cover_image'],
            #         use_container_width=True)  # Replace 'cover_image' with the actual key for the image URL

            # Display the song title and artist
            st.write(f"**{track['top_song']}** by {track['artist']}")

            # Add a button to listen to the track preview

            preview_url = get_track_preview(track['deezer_id'])  # Fetch the preview URL from Deezer
            print(preview_url)
            if preview_url:  # Check if preview_url exists
                st.audio(preview_url, format='audio/mp3')  # Play the preview
            else:
                st.error("No preview available for this track.")

    st.session_state.recommendations_shown = True


if st.session_state.listening:
    st.subheader(f"Now playing: {st.session_state.current_track_name}")
    st.audio(st.session_state.current_track_url, format='audio/mp3') # Adjust format as needed
    time.sleep(30)  # Stream for 30 seconds
    st.session_state.listening = False
    st.session_state.recommendations_shown = True  # Return to recommendations after 30 seconds

# Playlist creation
if st.session_state.recommendations_shown and not st.session_state.playlist:
    st.subheader('Create a playlist of three song between the one proposed. Choose the one that you liked the most! Remeber to click on the **Create the Playlist** button.')


    # Feedback on Known Songs
    playlists = {}
    feedback_data = []

    # Create a grid layout for displaying songs
    cols = st.columns(3)  # Create 3 columns for the grid
    col_index = 0  # Initialize column index

    for track in st.session_state.combined_list:
        # Determine if the track is from known_list or u_list for unique keys
        if track in st.session_state.known_list:
            source = 'Known List'
        else:
            source = 'Unknown List'

        # Display the cover image and checkbox in the appropriate column
        with cols[col_index]:
            # Assuming track has a 'cover_image' key for the image URL
            st.image(track['cover_image'], use_container_width=True)  # Display the cover image

            # Create a checkbox with a condition to limit selections
            if st.session_state.selected_count < 3:
                song = st.checkbox(f"- {track['top_song']} by {track['artist']}", key=track['top_song'])
            else:
                # If the limit is reached, disable the checkbox
                song = st.checkbox(f"- {track['top_song']} by {track['artist']}", value=False, disabled=True,
                                   key=track['top_song'])

            # Update the selected count based on the checkbox state
            if song:
                if st.session_state.selected_count < 3:
                    st.session_state.selected_count += 1
            else:
                # If the song is unchecked, decrease the count
                if st.session_state.selected_count > 0:
                    st.session_state.selected_count -= 1

            # Store the song in the playlists dictionary
            playlists[track['top_song']] = song

            # Store feedback data for each track
            feedback_data.append({
                'Playlist': song,
                'Source': source  # Indicate the source
            })

        # Update column index for the next iteration
        col_index += 1
        if col_index >= 3:  # Reset column index after 3 columns
            col_index = 0

    if st.button("Create the playlist!"):
        feedback_df = pd.DataFrame(feedback_data)
        feedback_df.to_csv("playlist.csv", mode='a', index=False)

        # Set flag to show message after rerun
        st.session_state.show_message = True
        st.session_state.sidebar_hidden = False
        st.session_state.playlist = True
        st.session_state.current_id += 1

        st.rerun()  # Rerun the app immediately

if st.session_state.show_message:
    st.success("Thank you for creating the playlist, now go to the **Questionnaire** page")
    st.session_state.show_message = False  # Reset flag so message doesn't persist forever


# Feedback Questionnaire

if st.session_state.feedback_submitted:
    reset = st.button("Finish Experiment")
    if reset:
        st.session_state.age = ""
        st.session_state.genre_input = ""
        st.session_state.artist_input = ""
        st.session_state.recommendations_shown = False  # Reset recommendations shown
        st.session_state.feedback_submitted = False  # Reset feedback submitted
        st.rerun()  # Rerun the app to refresh










