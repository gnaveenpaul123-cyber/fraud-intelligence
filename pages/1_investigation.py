import streamlit as st

st.set_page_config(layout="wide")

st.title("🛡 Investigation Progress")

progress = st.progress(45)

st.write("Current Stage")

st.info("Running OCR on downloaded images...")

st.write("")

st.write("✔ Reddit Posts Collected")

st.write("✔ Images Downloaded")

st.write("⏳ OCR Extraction")

st.write("○ Entity Extraction")

st.write("○ AI Scam Analysis")

st.write("○ Screenshot Capture")

st.write("○ Excel Report")