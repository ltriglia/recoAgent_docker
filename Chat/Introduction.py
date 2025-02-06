import streamlit as st
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

st.set_page_config(
    page_title="Introduction",
)

st.write("# Musical Taste Chat")


st.markdown(
    """
    We invite you to participate in a brief experiment where you'll discuss yourself and your musical preferences.
    This information will assist the agent in creating a personalized song list for you. 
    After that, you'll have the opportunity to listen to the songs and choose three to add to a playlist. 
    Thank you for your participation!
"""
)

user_session_id = _get_session()

data_directory = os.path.join("Form", "data", f"{user_session_id}")  # Move up one directory to Form

# Create the directory if it doesn't exist
os.makedirs(data_directory, exist_ok=True)
id = st.text_input("Please enter your Prolific ID")
if st.button("Submit"):
    feedback_file_path = os.path.join(data_directory, f"prolific_id_{user_session_id}.txt")
    with open(feedback_file_path, "a") as f:  # Append mode
        f.write(id + "\n")

    st.markdown("To start the experiment, please select the **Chat with me!** page.")