import pandas as pd
import streamlit as st
import os
import random


def _get_session():
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_id


# Function to handle form submission
def handle_form_submission():
    new_song_preferences = pd.DataFrame.from_records([
        {'song': song, 'knows_song': data['knows_song'], 'like_rating': data['like_rating']}
        for song, data in st.session_state.preferences.items()
    ])

    # Concatenate the new preferences with the existing DataFrame
    st.session_state.song_preferences_df = pd.concat([st.session_state.song_preferences_df, new_song_preferences],
                                                     ignore_index=True)
    try:
        st.session_state.song_preferences_df.to_csv(song_preferences_file_path, index=False)
        print("Files song saved successfully.")
    except Exception as e:
        print(f"Error saving files: {e}")
    st.session_state["stage"] = "adjective_form"

def handle_final():
    new_adjective_ratings = pd.DataFrame.from_records([
        {'adjective_pair': f"{adj_left} vs {adj_right}", 'adjective_rating': rating}
        for (adj_left, adj_right), rating in st.session_state.selections.items()
    ])

    # Concatenate the new ratings with the existing DataFrame
    st.session_state.adjective_ratings_df = pd.concat([st.session_state.adjective_ratings_df, new_adjective_ratings],
                                                      ignore_index=True)

    try:
        st.session_state.adjective_ratings_df.to_csv(adjective_ratings_file_path, index=False)
        print("Files adj saved successfully.")
    except Exception as e:
        print(f"Error saving files: {e}")
    st.session_state["stage"] = "last_stage"
if "sidebar_hidden" not in st.session_state:
    st.session_state.sidebar_hidden = True
if "stage" not in st.session_state:
    st.session_state["stage"] = "song_form"
    st.session_state.sidebar_hidden = True

user_session_id = _get_session()

data_directory = os.path.join("Form", "data", f"{user_session_id}")  # Move up one directory to Form

# Create the directory if it doesn't exist
os.makedirs(data_directory, exist_ok=True)

if 'song_preferences_df' not in st.session_state:
    st.session_state.song_preferences_df = pd.DataFrame(columns=['song', 'knows_song', 'like_rating'])

if 'adjective_ratings_df' not in st.session_state:
    st.session_state.adjective_ratings_df = pd.DataFrame(columns=['adjective_pair', 'adjective_rating'])

if 'preferences' not in st.session_state:
    st.session_state.preferences = {}
if 'selections' not in st.session_state:
    st.session_state.selections = {}


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

song_preferences_file_path = os.path.join(data_directory, f"song_preferences_{user_session_id}.csv")
adjective_ratings_file_path = os.path.join(data_directory, f"adj_rating_{user_session_id}.csv")
st.title("Questionnaire")


if st.session_state["stage"] == "song_form":
    with st.form(key='song_form'):
        st.write(
            "You will be asked to fill out two questionnaires. The first one will inquire about the songs you recognized "
            "and your level of enjoyment for each. The second questionnaire will focus on your recent "
            "interaction and how you would describe it. Finally, there will be an option to let the researcher know if "
            "anything did not function properly. Thank you for your collaboration!")
        st.write("Please indicate whether you knew the proposed songs and how much you enjoyed them.")

        preferences = {}
        for track in st.session_state.combined_list:
            knows_song = st.radio(
                f"Do you know the song '{track['top_song']}' by {track['artist']}?",
                options=["Yes", "No"],
                key=track
            )
            like_rating = st.slider(f"How much do you like '{track['top_song']}'?", min_value=0, max_value=10, value=5,
                                    step=1)
            preferences[track['top_song']] = {
                'knows_song': knows_song,
                'like_rating': like_rating
            }

        song_submit = st.form_submit_button("Submit")

    if song_submit:
        st.session_state.preferences = preferences
        st.success("Thank you for the feedback!")
        handle_form_submission()
        st.rerun()


if st.session_state["stage"] == "adjective_form":
    with st.form(key='adjective_form'):
        st.write("Thinking about the experience lived, how you will describe it? Choose the adjective that best fits between the one proposed.")

        # Pairs of adjectives
        adjectives = [
            ("Confusing", "Clear"),
            ("Easy to learn", "Difficult to learn"),
            ("Complicated", "Easy"),
            ("Not understandable", "Understandable"),
            ("Usual", "Leading edge"),
            ("Dull", "Creative"),
            ("Conservative", "Innovative"),
            ("Conventional", "Inventive"),
            ("Demotivating", "Motivating"),
            ("Boring", "Exciting"),
            ("Inferior", "Valuable"),
            ("Not interesting", "Interesting"),
            ("Obstructive", "Supportive"),
            ("Does not meet the expectations", "Meets the expectations"),
            ("Unpredictable", "Predictable"),
            ("Not secure", "Secure"),
            ("Inefficient", "Efficient"),
            ("Slow", "Fast"),
            ("Cluttered", "Organized"),
            ("Impractical", "Practical"),
            ("Human", "System")
        ]
        random.shuffle(adjectives)
        # Store user selections
        selections = {}

        for adj_left, adj_right in adjectives:
            option_mapping = {
                adj_left: 1,  # Not
                "Slightly": 2,  # Slightly Not
                "Somewhat": 3,  # Somewhat Not
                "Neutral": 4,  # Neutral
                "Somewhat": 5,  # Somewhat
                "Slightly": 6,  # Slightly
                adj_right: 7  # Very
            }

            # Create a select slider for each pair of adjectives
            selection = st.select_slider(
                f"Rate between '{adj_left}' and '{adj_right}'",
                options=[
                    adj_left,  # Not
                    "Slightly",  # Slightly Not
                    "Somewhat",  # Somewhat Not
                    "Neutral",  # Neutral
                    "Somewhat",  # Somewhat
                    "Slightly",  # Slightly
                    adj_right  # Very
                ],
                value="Neutral"
            )

            # Save the selection using the mapping
            selections[(adj_left, adj_right)] = option_mapping[selection]

        # submit_button:

        submit = st.form_submit_button(label='Submit')

    if submit:
        st.session_state.selections = selections
        st.success("Thank you for you time!")
        handle_final()
        st.rerun()

if st.session_state["stage"] == "last_stage":
    user_feedback = st.text_input(
        "Please let us know if anything didn't function properly, and thank you for your understanding")
    feedback_file_path = os.path.join(data_directory, f"user_feedback_{user_session_id}.txt")
    with open(feedback_file_path, "a") as f:  # Append mode
        f.write(user_feedback + "\n")
    finish_experiment = st.button("Finish experiment")
    if finish_experiment:
        st.subheader("Thank you for participating in this experiment.")
        st.markdown("**Completion code Prolific**: C1CSP3Y6 ")



