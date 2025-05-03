import streamlit as st
import os
from datetime import datetime
import urllib.parse

# Set page config
st.set_page_config(
    layout="wide",
    page_title="Transcript Chat",
    page_icon="💬"
)

# Function to create UI Grid
def make_grid(cols, rows):
    return [st.columns(rows) for _ in range(cols)]

# Initialize session state for chat history if not exists
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get transcript from query parameters
transcript_text = ""
if "transcript" in st.query_params:
    encoded_transcript = st.query_params["transcript"]
    transcript_text = urllib.parse.unquote(encoded_transcript)
    # Store in session state for persistence
    st.session_state["transcript_text"] = transcript_text

# Main UI
st.title("Transcript Chat 💬")

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

# Check if transcript is available
if not transcript_text and ("transcript_text" not in st.session_state or not st.session_state["transcript_text"]):
    st.warning("No transcript available. Please transcribe a video first.")
    st.info("Go to the 'Transcribe YouTube Video' page to transcribe a video.")
    st.stop()

# Use transcript from query params or session state
transcript_to_use = transcript_text if transcript_text else st.session_state["transcript_text"]

# Display transcript info
st.markdown("### Current Transcript")
with st.expander("View Transcript"):
    st.text_area("Transcript", transcript_to_use, height=200)

# Chat interface
st.markdown("""
#### Chat with Your Transcript
Ask questions about the transcript or request bullet points.

**Examples:**
- "What are the main topics discussed?"
- "Give me bullet points of the key concepts"
- "Summarize the technical details"
- "What did they say about [specific topic]?"
""")

# Unified chat function that handles both regular questions and bullet points
def chat_response(transcript, query):
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Check if the query is asking for bullet points
    bullet_keywords = ["bullet point", "bullet points", "list", "summarize", "key points", "main points", "highlight"]
    is_bullet_request = any(keyword in query_lower for keyword in bullet_keywords)
    
    # Split transcript into sentences
    sentences = transcript.split('.')
    
    # Find sentences that contain keywords from the query
    relevant_sentences = []
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in query_lower.split()):
            relevant_sentences.append(sentence.strip())
    
    # If no relevant sentences found, return a generic response
    if not relevant_sentences:
        return "I couldn't find specific information about that in the transcript. Try asking about a different topic or using different keywords."
    
    # If it's a bullet point request, format as bullet points
    if is_bullet_request:
        bullet_points = ""
        for i, sentence in enumerate(relevant_sentences[:5]):
            bullet_points += f"• {sentence}\n\n"
        return bullet_points
    
    # Otherwise, return as regular chat response
    return "Here's what I found in the transcript:\n\n" + "\n\n".join(relevant_sentences[:3])

# Create a form for the chat interface
with st.form(key="chat_form"):
    user_input = st.text_input("Ask anything about the transcript:")
    submit_button = st.form_submit_button(label="Ask")
    
    if submit_button and user_input:
        # Get response from unified chat function
        response = chat_response(transcript_to_use, user_input)
        
        # Add to chat history
        st.session_state.chat_history.append({
            "user": user_input,
            "ai": response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

# Display chat history in a separate container
history_container = st.container()
with history_container:
    if st.session_state.chat_history:
        st.markdown("### Chat History")
        for item in reversed(st.session_state.chat_history):
            with st.expander(f"Q: {item['user']} ({item['timestamp']})"):
                st.markdown(f"**You:** {item['user']}")
                st.markdown(f"**AI:** {item['ai']}")

# Add a button to clear chat history
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.success("Chat history cleared!") 