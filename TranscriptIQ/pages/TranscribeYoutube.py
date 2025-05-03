import streamlit as st
import os
import sys
from datetime import datetime
from io import BytesIO
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pyecharts.charts import WordCloud, Gauge
from pyecharts import options as opts
from collections import Counter
from annotated_text import annotated_text
from dataclasses import dataclass
from typing import Literal
import streamlit.components.v1 as components
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
from nltk import sent_tokenize
import urllib.parse
from moviepy.video.io.VideoFileClip import VideoFileClip

# Import functions
from myfunctions.my_functions import (
    get_video_info, current_directory, create_folder_and_directories,
    download_youtube, rename_videos, mp4_to_mp3, transcribe_mp3, download_youtube1,
    split_video_into_segments, transcribe_video_segments
)
from myfunctions.my_summarization_functions import summarize_with_huggingface

# Import LangChain
from langchain_openai import ChatOpenAI  # ✅ Correct import
from langchain_core.callbacks import CallbackManager
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory  # ✅ Better for handling chat history

# Streamlit Config
st.set_page_config(layout="wide", page_title="Transcribe YouTube Video", page_icon="🎥")

# Initialize session state variables
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

# Function to create UI Grid
def make_grid(cols, rows):
    return [st.columns(rows) for _ in range(cols)]

# Main UI
st.title("Transcribe YouTube Video 🎥")

# Add a button to go back to the home page
st.markdown("""
<a href="../" target="_self">
    <button style="
        background-color: #f0f2f6;
        border: none;
        color: #31333F;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    ">
        ← Back to Home
    </button>
</a>
""", unsafe_allow_html=True)

# Create directories
current_directory(3)

# YouTube Input
video_url = st.text_input("YouTube Link", "https://www.youtube.com/watch?v=iwNO4nbmkVs")

# Add segment duration option for longer videos
segment_duration = st.slider(
    "Segment Duration (minutes)", 
    min_value=5, 
    max_value=30, 
    value=10,
    help="For longer videos, split into segments of this duration for better transcription"
)

# Language selection
language_options = {
    "Auto-detect": None,
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn"
}

# Add transcription quality settings
st.sidebar.markdown("### Transcription Settings")
selected_language = st.sidebar.selectbox(
    "Select Language (optional)",
    options=list(language_options.keys()),
    help="Select the language of the video for better transcription accuracy"
)

# Add a note about transcription quality
st.sidebar.info("""
**Transcription Quality Tips:**
- Select the correct language for better accuracy
- For longer videos, use smaller segment sizes
- Clear audio will result in better transcription
- The 'large' Whisper model is used for maximum accuracy
""")

youtube_button = st.button("Transcribe")

if youtube_button:
    info = get_video_info(video_url)
    st.markdown(f"#### {info['title']}")

    # Create Grid Layout
    grid_video = make_grid(1, 6)
    with grid_video[0][0]:
        st.markdown(f"**Views**  \n#### {info.get('views', 'N/A')}")
    with grid_video[0][1]:
        st.markdown(f"**Length**  \n#### {info.get('duration', 'N/A')} sec.")
    with grid_video[0][2]:
        st.markdown(f"**Author**  \n#### {info.get('author', 'N/A')}")
    with grid_video[0][3]:
        st.markdown(f"**Video ID**  \n#### {info.get('video_id', 'N/A')}")
    with grid_video[0][4]:
        try:
            publish_date = datetime.strptime(info['publish_date'], '%Y%m%d').strftime('%Y-%m-%d')
        except (ValueError, KeyError, TypeError):
            publish_date = info.get('publish_date', 'Unknown Date')
        st.markdown(f"**Published**  \n#### {publish_date}")
    with grid_video[0][5]:
        st.image(info.get('thumbnail_url', ''))

    if info.get("age_restricted", False):
        st.warning("This video is age-restricted. The application will stop at this point.", icon="⚠️")
        st.stop()
    
    # Create necessary directories
    mp4_directory, mp3_directory, txt_directory = create_folder_and_directories()

    # Download Video
    with st.spinner("Downloading YouTube video as MP4..."):
        try:
            video_extension = download_youtube(video_url, mp4_directory)
        except Exception as e:
            st.warning(f"⚠️ Error downloading MP4: {e}. Trying WebM format instead...")
            video_extension, duration = download_youtube1(video_url, mp4_directory)

    # ✅ Ensure at least one valid video file exists
    video_files = [f for f in os.listdir(mp4_directory) if f.endswith((".mp4", ".mkv", ".webm"))]
    if not video_files:
        st.error("❌ No video file found in the downloads folder!")
        st.stop()

    video_mp4 = os.path.join(mp4_directory, video_files[0])
    st.write(f"🔍 Using video file: {video_mp4}")

    if not os.path.exists(video_mp4):
        st.error(f"❌ Video file not found: {video_mp4}")
        st.stop()

    # Rename Videos (after confirming existence)
    rename_videos(mp4_directory)

    # Check video duration and decide whether to split into segments
    video = VideoFileClip(f"{mp4_directory}/video.{video_extension}")
    duration = video.duration
    video.close()
    
    # Convert segment duration from minutes to seconds
    segment_duration_seconds = segment_duration * 60
    
    # Determine if we need to split the video
    if duration > segment_duration_seconds:
        st.info(f"Video is {duration:.1f} seconds long. Splitting into segments of {segment_duration_seconds} seconds for better transcription.")
        
        # Split video into segments
        with st.spinner(f"Splitting video into segments of {segment_duration} minutes..."):
            segment_paths = split_video_into_segments(mp4_directory, video_extension, segment_duration_seconds)
            st.success(f"Video split into {len(segment_paths)} segments successfully!")
        
        # Transcribe segments
        with st.spinner("Transcribing video segments..."):
            selected_lang_code = language_options[selected_language]
            result = transcribe_video_segments(segment_paths, mp3_directory, selected_lang_code)
    else:
        # Convert Video to Audio
        with st.spinner("Converting MP4 to MP3..."):
            mp4_to_mp3(mp4_directory, video_extension, mp3_directory)

        # Transcription
        with st.spinner("Transcribing YouTube Video..."):
            selected_lang_code = language_options[selected_language]
            result = transcribe_mp3(mp3_directory, "my_audio", language=selected_lang_code)

    # Display audio player
    col1, col2 = st.columns(2)
    if os.path.exists(f"{mp3_directory}/my_audio.mp3"):
        col2.audio(f"{mp3_directory}/my_audio.mp3")

    # WebVTT Format
    WebVTT = "WEBVTT"
    with col1:
        st.info(f"Detected language: {result['language']}")
        for segment in result["segments"]:
            start, end, text = segment["start"], segment["end"], segment["text"]
            WebVTT += f"\n[{start:.2f} : {end:.2f}] : {text}"
        user_text = st.text_area("Full Transcript", result["text"], height=450)

    with st.expander("WebVTT Format"):
        st.text_area("Web Video Text Tracks (WebVTT)", WebVTT, height=200)

    col2.video(video_url)
    st.download_button("Download Transcript", result["text"], f"Transcript_{datetime.now()}.txt", "text/plain")
     
    # Store transcript text in session state for other pages
    st.session_state["transcript_text"] = result["text"]
    st.session_state["summary"] = summarize_with_huggingface(result["text"])
    
    # Sentiment Analysis
    st.markdown("### Sentiment Analysis 😃 😶 😡")
    analyser = SentimentIntensityAnalyzer()
    score = analyser.polarity_scores(result["text"])
    polarity = score["compound"]

    st.markdown(f"#### Sentiment Score: {polarity}")
    sentiment_text = "Positive 😊" if polarity > 0 else "Neutral 😐" if polarity == 0 else "Negative 😠"
    st.write(f"Sentiment: {sentiment_text}")
    
    # Add a button to redirect to the TranscriptChat page at the end
    st.markdown("### Ask Questions About Your Transcript")
    st.info("Click the button below to go to the Transcript Chat page where you can ask questions about your transcript.")
    
    # Use a direct link with query parameters instead of st.switch_page
    encoded_transcript = urllib.parse.quote(result["text"][:1000])  # Encode first 1000 chars to avoid URL length issues
    chat_url = f"TranscriptChat?transcript={encoded_transcript}"
    
    st.markdown(f"""
    <a href="{chat_url}" target="_self">
        <button style="
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        ">
            ASK Queries
        </button>
    </a>
    """, unsafe_allow_html=True)
