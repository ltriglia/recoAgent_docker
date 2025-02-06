import pandas as pd
import streamlit as st
import os
import random


# Create a form
def _get_session():
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_id

def handle_form_song():
    # Append song preferences to the DataFrame
    new_song_preferences = pd.DataFrame.from_records([
        {'song': song, 'knows_song': data['knows_song'], 'like_rating': data['like_rating']}
        for song, data in preferences.items()
    ])

    # Concatenate the new preferences with the existing DataFrame
    st.session_state.song_preferences_df = pd.concat([st.session_state.song_preferences_df, new_song_preferences],
                                                     ignore_index=True)
    try:
        st.session_state.song_preferences_df.to_csv(song_preferences_file_path, index=False)
        print("Files saved successfully.")
    except Exception as e:
        print(f"Error saving files: {e}")

    st.session_state["stage"] = "adjective_form"

def handle_adj_form():

    new_adjective_ratings = pd.DataFrame.from_records([
        {'adjective_pair': f"{adj_left} vs {adj_right}", 'adjective_rating': rating}
        for (adj_left, adj_right), rating in selections.items()
    ])

    # Concatenate the new ratings with the existing DataFrame
    st.session_state.adjective_ratings_df = pd.concat([st.session_state.adjective_ratings_df, new_adjective_ratings],
                                                      ignore_index=True)
    try:
        st.session_state.adjective_ratings_df.to_csv(adjective_ratings_file_path, index=False)
        print("Files saved successfully.")
    except Exception as e:
        print(f"Error saving files: {e}")

    st.session_state["stage"] = "agent_form"

def handle_agent_form():
    df = pd.DataFrame(selections.items(), columns=['Attribute', 'Value'])
    df.to_csv(agent_rating_file_path, mode='a', header=False, index=False)

    st.session_state["stage"] = "last_stage"

user_session_id = _get_session()

data_directory = os.path.join("Chat", "data", f"{user_session_id}")  # Move up one directory to Form

# Create the directory if it doesn't exist
os.makedirs(data_directory, exist_ok=True)

if 'song_preferences_df' not in st.session_state:
    st.session_state.song_preferences_df = pd.DataFrame(columns=['song', 'knows_song', 'like_rating'])

if 'adjective_ratings_df' not in st.session_state:
    st.session_state.adjective_ratings_df = pd.DataFrame(columns=['adjective_pair', 'adjective_rating'])
if "sidebar_hidden" not in st.session_state:
    st.session_state.sidebar_hidden = True
if "stage" not in st.session_state:
    st.session_state["stage"] = "song_form"
    st.session_state.sidebar_hidden = True

if 'preferences' not in st.session_state:
    st.session_state.preferences = {}
if 'selections' not in st.session_state:
    st.session_state.selections = {}
if 'selections_agent' not in st.session_state:
    st.session_state.selections_agent = {}

st.session_state.sidebar_hidden = True
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
agent_rating_file_path = os.path.join(data_directory, f"agent_rating_{user_session_id}.csv")

# Title of the app
st.title("Questionnaire")

# Create a form
attributes = ["I will use the agent again in the future",
              "I can see myself using the agent in the future",
              "I oppose further interaction with the agent",
              "The agent is boring",
              "It is interesting to interact with the agent",
              "I enjoy interacting with the agent",
              "The agent is unpleasant to deal with",
              "I was concentrated during the interaction with the agent",
              "The interaction captured my attention",
              "I was alert during the interaction with the agent",
              "The agent always gives good advice",
              "The agent acts truthfully",
              "I can rely on the agent",
              "The agent and I have a strategic alliance",
              "Collaborating with the agent is like a joint venture",
              "The agent joins me for mutual benefit",
              "The agent can collaborate in a productive way",
              "The agent and I are in sync with each other",
              "The agent understands me",
              "The agent remains focused on me throughout the interaction",
              "The agent is attentive",
              "I receive the agent's full attention throughout the interaction",
              "The agent's behavior does not make sense",
              "The agent's behavior is irrational",
              "The agent is inconsistent",
              "The agent appears confused",
              "The agent acts intentionally",
              "The agent knows what it is doing",
              "The agent has no clue of what it is doing",
              "The agent can make its own decision",
              "I see the interaction with the agent as something positive",
              "I view the interaction as something favorable",
              "I think negatively of the interaction with the agent",
              "My friends would recommend me to use the agent",
              "Others would encourage me to use the agent",
              "The agent makes me look good",
              "People would look favorably at me because of my interaction with the agent",
              "Select +3 to demonstrate your attention"]  # Add your attributes here
random.shuffle(attributes)
print(st.session_state["stage"])
if st.session_state["stage"] == "song_form":
    with st.form(key='song_form'):
        st.write("You will be required to complete three questionnaires. "
                 "The first will ask about the songs you recognized and your level of enjoyment for each. The second "
                 "questionnaire will focus on your recent interaction and how you would describe it. "
                 "The third will gather your impressions regarding the collaboration in the chat. "
                 "Lastly, there will be an option to inform the researcher if anything did not work as intended. "
                 "Thank you for your participation!")
        st.write("Please indicate whether you knew the proposed songs and how much you enjoyed them."
                 "Please use the checkbox to indicate if you know the song or not")

        preferences = {}
        for track in st.session_state.combined_list:
            knows_song = st.checkbox(f"Do you know the song '{track['top_song']}' by {track['artist']}?", key=track)
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
        handle_form_song()
        st.rerun()

if st.session_state["stage"] == "adjective_form":
    with st.form(key='adjective_form'):

        st.write("Please describe the completed interaction by selecting the adjectives that best represent it.")

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
            ("Boring", "Exiting"),
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
                adj_left: -3,  # Not
                "Slightly": -2,  # Slightly Not
                "Somewhat": -1,  # Somewhat Not
                "Neutral": 0,  # Neutral
                "Somewhat": 1,  # Somewhat
                "Slightly": 2,  # Slightly
                adj_right: 3  # Very
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
            st.session_state.selections[(adj_left, adj_right)] = option_mapping[selection]

        adj_submit = st.form_submit_button(label='Submit')

        if adj_submit:
            st.session_state.selections = selections
            st.success("Thank you for you time!")
            handle_adj_form()
            st.rerun()

if st.session_state["stage"] == "agent_form":
    with st.form(key='agent_form'):
        # Loop through each attribute to create a radio button
        st.write("Kindly express how much you agree with the following sentences about the interaction with the agent."
                 "The scale ranges from -3"
                 " to +3, where -3 indicates disagreement, 0 signifies neither agree nor disagree, and +3 represents agreement")
        selections = {}
        for attribute in attributes:
            selections[attribute] = st.radio(attribute, options=[-3, -2, -1, 0, 1, 2, 3], index=3, horizontal=True)

        # Submit button

        agent_submit = st.form_submit_button(label='Submit')

        if agent_submit:
            st.session_state.selections_agent = selections
            st.success("Thank you for participating!")
            handle_agent_form()
            st.rerun()

if st.session_state["stage"] == "last_stage":
    user_feedback = st.text_input(
        "Please let us know if anything didn't function properly, and thank you for your understanding")
    feedback_file_path = os.path.join(data_directory, f"user_feedback_{user_session_id}.txt")
    with open(feedback_file_path, "a") as f:  # Append mode
        f.write(user_feedback + "\n")
    finish_experiment = st.button("Finish experiment")
    if finish_experiment:
        st.subheader("Thank you for participating in this experiment. You can close this window now.")


