import os
import streamlit as st
from langchain_openai import AzureChatOpenAI
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import re
import ast
import html
import requests
import random
import threading
import sys
from openai import AzureOpenAI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.agent import Agent

def _get_session():
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_id

## Functions to get info about the songs
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


def fetch_artist_data(artist_name, known_list, u_list):
    artist_id = get_artist_id(artist_name)
    top_songs_first_three, top_songs_last_three = get_top_songs_from_ranked_artists(artist_id, limit=15)
    known_list.extend(top_songs_first_three)
    u_list.extend(top_songs_last_three)

def search_deezer_track(track_name, artist_name):
    """Search for a track on Deezer and return its ID."""
    search_url = f"https://api.deezer.com/search?q={track_name} {artist_name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['id']  # Return the first track's ID found
    return None

def get_track_preview(deezer_id):
    """Fetch track details from Deezer and return the preview URL."""
    track_url = f"https://api.deezer.com/track/{deezer_id}"
    response = requests.get(track_url)

    if response.status_code == 200:
        data = response.json()
        preview_url = data.get('preview')  # Attempt to get the preview URL
        return preview_url  # Return the preview URL
    else:
        print(f"Error: {response.status_code}")  # Print error status if not 200
    return None




def construct_prompt(stage):
    if stage == 'ask_age':
        return "Hey! Great to meet you! Today, we’re going to listen to some songs together and build a playlist of your favorites. But first, let’s start with a question: How old are you?"
    elif stage == 'ask_genres':
        return "Awesome! Now that I know your age, let's dive into music! Please tell me your three favorite music genres. I can't wait to hear them!"
    elif stage == 'ask_artists':
        return "Great choices! Now, please name three of your favorite artists. I'm excited to learn about your taste in music!"

    return ""


def update_state_from_llm_response(user_input):
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Update the stage and user_info based on the user input
    if st.session_state.stage == 'ask_age':
        response_content = agent.validate_response(st.session_state.stage, user_input)
        print(response_content)

        # Append user input and LLM response to chat history
        st.session_state.chat_history.append({"user": user_input, "bot": response_content})

        if "yes" in response_content.lower():  # Check if the response indicates validity
            age = int(re.findall(r'\d+', user_input)[0])  # Extract the first number
            st.session_state.user_info['age'] = age  # Store the age
            st.session_state.stage = 'ask_genres'  # Move to the next stage
            print("Valid age input. Stage updated to ask_genres.")
        else:
            # Create context from chat history for re-prompt
            response_content = agent.alternative_response(st.session_state.stage, st.session_state.chat_history)
            st.session_state.chat_history.append({"user": user_input, "bot": response_content})
            print("Invalid age input. Asking again.")
            return response_content  # Return the re-prompt to be displayed

    elif st.session_state.stage == 'ask_genres':
        response_content = agent.validate_response(st.session_state.stage, user_input)
        print(response_content)
        # Append user input and LLM response to chat history
        st.session_state.chat_history.append({"user": user_input, "bot": response_content})

        if "yes" in response_content.lower():  # Check if the response indicates validity
            genres = agent.extraction_response(response_content, st.session_state.chat_history, st.session_state.stage)
            decoded_genres = html.unescape(genres)
            decoded_genres = decoded_genres.replace('`', '').replace('python', '').strip()
            print("Decoded genres: ", decoded_genres)
            # Remove any leading variable assignment if present
            if decoded_genres.startswith("genres = "):
                decoded_genres = decoded_genres[len("genres = "):].strip()

            if decoded_genres.startswith("[") and decoded_genres.endswith("]"):
                # It's already in list format
                pass
            elif decoded_genres.startswith('"') and decoded_genres.endswith('"'):
                # It's a single string, wrap it in a list
                decoded_genres = f'["{decoded_genres[1:-1]}"]'
            else:
                # If it's a single element without quotes, wrap it in a list
                decoded_genres = f'["{decoded_genres}"]'
            try:
                # Use ast.literal_eval to safely evaluate the string as a Python literal
                genres_list = ast.literal_eval(decoded_genres)

                # Ensure genres_list is indeed a list
                if isinstance(genres_list, list):
                    # Store the list directly in session state
                    st.session_state.user_info['genres'] = genres_list
                else:
                    st.error("The extracted genres are not in a valid list format.")
            except (ValueError, SyntaxError) as e:
                print(f"Error parsing genres: {e}")

            st.session_state.stage = 'ask_artists'  # Move to the next stage
            print("Valid genres input. Stage updated to listening.")

        else:
            # Create context from chat history for re-prompt
            response_content = agent.alternative_response(st.session_state.stage, st.session_state.chat_history)
            st.session_state.chat_history.append({"user": user_input, "bot": response_content})
            print("Invalid genres input. Asking again.")
            return response_content  # Return the re-prompt to be displayed

    elif st.session_state.stage == 'ask_artists':
        response_content = agent.validate_response(st.session_state.stage, user_input)
        # Append user input and LLM response to chat history
        st.session_state.chat_history.append({"user": user_input, "bot": response_content})

        if "yes" in response_content.lower():  # Check if the response indicates validity
            artists = agent.extraction_response(response_content, st.session_state.chat_history,st.session_state.stage)
            print("Extracted artists: ", artists)


            decoded_artists = artists

            print("Decoded artists output:", decoded_artists)

            # Remove any leading variable assignment if present
            if decoded_artists.startswith("artists = "):
                decoded_artists = decoded_artists[len("artists = "):].strip()

            # Now decoded_artists should look like: '["pop"]'

            # Check if the output is a single element or a list
            if decoded_artists.startswith("[") and decoded_artists.endswith("]"):
                # It's already in list format
                pass
            else:
                # It's a single element, wrap it in a list format
                decoded_artists = f"[{decoded_artists}]"

            try:
                # Use ast.literal_eval to safely evaluate the string as a Python literal
                artists_list = ast.literal_eval(decoded_artists)

                # Ensure genres_list is indeed a list
                if isinstance(artists_list, list):
                    # Store the list directly in session state
                    if len(artists_list) > 3:
                        artists_list = artists_list[:3]
                    st.session_state.user_info['artists'] = artists_list
                else:
                    st.error("The extracted artists are not in a valid list format.")
            except (ValueError, SyntaxError) as e:
                print(f"Error parsing genres: {e}")
            st.session_state.stage = 'listening'

            print("Valid artists input. Stage updated to listening.")

        else:
            # Create context from chat history for re-prompt
            response_content = agent.alternative_response(st.session_state.stage, st.session_state.chat_history)
            st.session_state.chat_history.append({"user": user_input, "bot": response_content})
            print("Invalid artists input. Asking again.")
            return response_content  # Return the re-prompt to be displayed

    elif st.session_state.stage == 'listening':
        print("In Listening")
        if 'artists' in st.session_state.user_info:
            with st.chat_message("assistant"):
                response_content = "This may take some time, but I'm looking at some songs that you might find interesting!  "
                st.write_stream(stream_data(response_content))
            artists = st.session_state.user_info['artists']
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
            print(st.session_state.combined_list)
            st.session_state.user_info['k_list'] = st.session_state.known_list
            st.session_state.user_info['u_list'] = st.session_state.u_list
            st.session_state.combined_list = st.session_state.known_list + st.session_state.u_list
            st.session_state.user_info['combined_list'] = st.session_state.combined_list
            st.session_state.user_info['current_index'] = st.session_state.current_index
            random.shuffle(st.session_state.combined_list)
            st.session_state.max_index = 5
            st.session_state.stage = 'suggestion'
            st.session_state.selected_count = 0
            return True


    elif st.session_state.stage == 'audio_play':
        st.session_state.current_index += 1
        like = False
        st.session_state.user_info['current_index'] = st.session_state.current_index
        if st.session_state.current_index <= st.session_state.max_index:
            track = st.session_state.combined_list[st.session_state.current_index]
            response_content = agent.validate_response(st.session_state.stage, user_input)
            print(track['top_song'])
            # Play the preview
            if "yes" in response_content.lower():
                like = True

                response_content = agent.suggestion_response(track, st.session_state.user_info, st.session_state.conversation,
                                                             like, user_input)

                st.session_state.stage = 'suggestion'
                return response_content

            else:

                response_content = agent.suggestion_response(track, st.session_state.user_info,
                                                             st.session_state.conversation,
                                                             like, user_input)

                st.session_state.chat_history.append({"user": user_input, "bot": response_content})
                print("Not like the suggestion.")
                st.session_state.stage = 'suggestion'
                return response_content
        else:
            response_content = agent.generate_response(st.session_state.stage, user_input)
            print("RESPONSE CONTENT PLAYLIST: ", response_content)
            st.session_state.stage = 'playlist_creation'
            return response_content
    return True


def stream_data(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.05)

# Streamlit app
def main():
    st.title("Musical taste Chat")
    if 'stage' not in st.session_state:
        st.session_state.stage = 'ask_age'
        st.session_state.user_info = {}
        st.session_state.recommendations = []
        st.session_state.conversation = []
        st.session_state.error_message = None
        st.session_state.feedback_submitted = False
        st.session_state.known_list = []
        st.session_state.u_list = []
        st.session_state.combined_list = []
        st.session_state.current_index = 0
        st.session_state.max_index = 0
        st.session_state.current_audio_url = None
        st.session_state.sidebar_hidden = True
        st.session_state.show_message = False
        # Display the initial prompt
        initial_prompt = construct_prompt(st.session_state.stage)
        st.session_state.conversation.append({"role": "assistant", "content": initial_prompt})

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
    data_directory = os.path.join("Chat", "prova", f"{user_session}")
    os.makedirs(data_directory, exist_ok=True)
    playlist_file_path = os.path.join(data_directory, f"playlist_{user_session}.csv")
    for message in st.session_state.conversation:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Your response:", key="input")
    if user_input:
        # Append user input to the conversation

        #if not any(entry['content'] == user_input for entry in st.session_state.conversation):
            # Append user input to the conversation
        #    st.session_state.conversation.append({"role": "user", "content": user_input})

            # Display the user input in the chat message
        #    with st.chat_message("user"):
        #        st.markdown(user_input)
        st.session_state.conversation.append({"role": "user", "content": user_input})

        # Display the user input in the chat message
        with st.chat_message("user"):
             st.markdown(user_input)
        print("Stage before update: ", st.session_state.stage)
        response_content = update_state_from_llm_response(user_input)

        if response_content is True:  # If the input was valid
            print("After update user_info: ", st.session_state.user_info)
            print("After update state: ", st.session_state.stage)

            response_content = agent.generate_response(st.session_state.stage, st.session_state.user_info)

            # Add the LLM response to the conversation
            st.session_state.conversation.append({"role": "assistant", "content": response_content})


            with st.chat_message("assistant"):
                st.write_stream(stream_data(response_content))


            print("Before if: ", st.session_state.stage)
            if st.session_state.stage == 'suggestion':
                st.session_state.user_info['current_index'] = st.session_state.current_index
                track = st.session_state.combined_list[st.session_state.current_index]
                preview_url = get_track_preview(track['deezer_id'])
                print("Current index first time: ", st.session_state.current_index)
                if st.session_state.current_index <= st.session_state.max_index:
                    if preview_url:  # Check if preview_url exists
                        st.audio(preview_url, format='audio/mp3')
                        st.session_state.stage = 'audio_play'
                else:
                    st.session_state.stage = 'playlist_creation'


        else:
            # If the response_content is not True, it means it's a re-prompt
            # Append the invalid response to the conversation
            st.session_state.conversation.append({"role": "assistant", "content": response_content})


            with st.chat_message("assistant"):
                st.write_stream(stream_data(response_content))
                

            print("Before if - like or not: ", st.session_state.stage)
            if st.session_state.stage == 'suggestion':
                print("Current index - at least second time: ", st.session_state.current_index)
                track = st.session_state.combined_list[st.session_state.current_index]
                preview_url = get_track_preview(track['deezer_id'])  # Fetch the preview URL from Deezer
                if st.session_state.current_index <= st.session_state.max_index:
                    if preview_url:  # Check if preview_url exists
                        st.session_state.current_audio_url = preview_url
                        st.audio(preview_url, format='audio/mp3')
                        st.session_state.stage = 'audio_play'
                else:
                    st.session_state.stage = 'playlist_creation'

    if st.session_state.stage == "playlist_creation":
        # Feedback on Known Songs
        with st.form("My_form"):
            st.markdown('**Check three songs that you want to add**')

            # Feedback on Known Songs
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

            playlist_submit = st.form_submit_button("Create the playlist!")

        if playlist_submit:
            feedback_df = pd.DataFrame(feedback_data)
            feedback_df.to_csv(playlist_file_path, mode='a',index=False)
            feedback_file_path = os.path.join(data_directory, f"conversation_{user_session}.txt")
            with open(feedback_file_path, "a", encoding='utf-8') as f:  # Use append mode
                for entry in st.session_state.conversation:
                    # Format each entry as "Role: Content"
                    f.write(f"{entry['role']}: {entry['content']}\n")
                f.write("\n")  # Add a newline after the conversation
            print("Conversation saved successfully!")
            st.session_state.show_message = True
            st.session_state.sidebar_hidden = False
            st.rerun()

    if st.session_state.show_message:
        st.success("Thank you for creating the playlist, now go to the **Questionnaire** page")
        st.session_state.show_message = False  # Reset flag so message doesn't persist forever
        st.session_state.stage = 'song_form'


# Set environment variables
os.environ["OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ('')

os.environ["LANGCHAIN_API_KEY"] = ""
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "chef_hat"

# Initialize the AzureChatOpenAI model
temperature = 1
max_tokens = 128
client = AzureOpenAI(
    api_key="",
    api_version="2024-08-01-preview",
    azure_endpoint="https://iitlines-swecentral1.openai.azure.com"
)

deployment_name = 'contact-Chefhat_gpt4omini'
agent = Agent(client, deployment_name)
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="56d77556acd24c079197b8c062f0f71f",
                                        client_secret="",
                                        redirect_uri="https://www.google.co.uk/",
                                        scope="user-library-read playlist-read-private user-read-private"))


if __name__ == "__main__":
    main()