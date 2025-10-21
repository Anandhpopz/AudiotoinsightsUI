import streamlit as st
import requests
from datetime import datetime
from sheet_insert import download_and_insert_excel  # your MongoDB function
import tempfile

st.set_page_config(page_title="Audio Transcription & Insights", page_icon="🎧", layout="centered")

# -----------------------------
# Streamlit UI Configuration
# -----------------------------
st.markdown("""
    <style>
    /* Your existing CSS here (unchanged) */
    /* ... */
    </style>
""", unsafe_allow_html=True)

# Logo + Header
logo_path = r"FMH New logo 24.png"
col1, col2 = st.columns([1, 4])
with col1:
    st.image(logo_path, width=150)
with col2:
    st.title("🎧 Audio Transcription & Insights")

st.markdown("Upload an audio file, get transcription & summary, and store Excel insights into MongoDB.")

API_URL = "https://audiotoinsights-fastapi.onrender.com/process_audio"
BASE_URL = "https://audiotoinsights-fastapi.onrender.com"

st.markdown('<div class="content-container">', unsafe_allow_html=True)

# -----------------------------
# File Upload Section
# -----------------------------
st.subheader("📁 Upload Audio File")
st.markdown("Support formats: WAV, MP3, M4A")
uploaded_file = st.file_uploader("", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    file_details = {
        "Filename": uploaded_file.name,
        "File size": f"{uploaded_file.size / 1024:.2f} KB",
        "Upload time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### File Details")
        for key, value in file_details.items():
            st.markdown(f"**{key}:** {value}")
    with col2:
        st.markdown("### Audio Preview")
        st.audio(uploaded_file, format="audio/wav")

    # -----------------------------
    # Process Audio Button
    # -----------------------------
    if st.button("🎯 Process Audio", help="Click to start processing the audio file"):
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(API_URL, files=files)

            if response.status_code == 200:
                data = response.json()

                # Save results in session_state
                st.session_state["download_url"] = data.get("download_url")
                st.session_state["transcription"] = data.get("transcription", "")
                st.session_state["summary"] = data.get("summary", "")

            else:
                st.error(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# -----------------------------
# Display Results (Persisted)
# -----------------------------
if "transcription" in st.session_state and st.session_state["transcription"]:
    st.subheader("🗣️ Malayalam Transcript with Timestamps")
    st.text_area("", value=st.session_state["transcription"], height=300, key="transcription_area")

if "summary" in st.session_state and st.session_state["summary"]:
    st.subheader("📝 Conversation Summary")
    st.text_area("", value=st.session_state["summary"], height=200, key="summary_area")

if "download_url" in st.session_state and st.session_state["download_url"]:
    full_download_url = f"{BASE_URL}{st.session_state['download_url']}"
    st.markdown(f'''
        <a href="{full_download_url}" class="download-button">📥 Download Excel Insights</a>
    ''', unsafe_allow_html=True)

    # -----------------------------
    # Add Rows to MongoDB
    # -----------------------------
    if st.button("📤 Add Rows to MongoDB", help="Download the Excel file and insert into MongoDB"):
        st.info("⏳ Downloading Excel and uploading to MongoDB...")
        try:
            result_msg = download_and_insert_excel(full_download_url)
            st.success(f"✅ {result_msg}")
        except Exception as e:
            st.error(f"❌ Failed to insert Excel data into MongoDB: {e}")
