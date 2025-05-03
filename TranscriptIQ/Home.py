import streamlit as st
from io import BytesIO
import os

# Set page config with proper static file configuration
st.set_page_config(
    layout="wide",
    page_title="TranscriptIQ",
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# Configure static file serving
if not os.path.exists('.streamlit'):
    os.makedirs('.streamlit')

# Main UI
st.title("TranscriptIQ 🎯")

st.markdown("""
## Welcome to TranscriptIQ!

TranscriptIQ is a powerful tool that helps you extract valuable insights from YouTube videos through transcription and AI-powered analysis.

### Features:
- **Transcribe YouTube Videos**: Convert video content to text with high accuracy
- **Highlight Answers**: Get AI-powered answers to your questions
- **Interactive AI Chat**: Ask questions and get detailed responses

### How to Use:
1. Go to the **Transcribe YouTube Video** page to transcribe a video
2. Once transcribed, you can:
   - Search for specific content
   - Ask questions about the transcript
   - Chat with the AI about the content

### Getting Started:
Click the button below to start transcribing!
""")

# Add a button to go to the TranscribeYoutube page using Streamlit's navigation
if st.button("Start Transcribing →", key="start_transcribing", 
             help="Click to go to the transcription page",
             use_container_width=False):
    st.switch_page("pages/TranscribeYoutube.py")

# Add a button to go to the TranscriptChat page
if st.button("Go to Chat →", key="go_to_chat", 
             help="Click to go to the chat page",
             use_container_width=False):
    st.switch_page("pages/TranscriptChat.py")
