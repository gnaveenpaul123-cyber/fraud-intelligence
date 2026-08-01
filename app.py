import streamlit as st
from controller import start_investigation
status_placeholder = st.empty()
st.set_page_config(
    page_title="Fraud Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide"
)
hide_streamlit_style = """
<style>

/* Hide the sidebar */
[data-testid="stSidebar"] {
    display: none;
}

/* Remove the empty space left by the sidebar */
[data-testid="stSidebarCollapsedControl"] {
    display: none;
}

/* Expand the main content */
[data-testid="stAppViewContainer"] > .main {
    margin-left: 0rem;
}

</style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)
if "screen" not in st.session_state:
    
    st.session_state.screen = "setup"
if "investigation_started" not in st.session_state:
    st.session_state.investigation_started = False
if st.session_state.screen == "setup":   
    st.title("fraudtraceAI")
    st.caption("Investigate Scams On Reddit. \n\n"
            "Confgure Your Investigation Below To Begin")


    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Posts Scanned", "0")
    with col2:
        st.metric("UPI IDs", "0")
    with col3:
        st.metric("AI Confirmed", "0")
    with col4:
        st.metric("Confidence", "--")
    left, right = st.columns([2, 1])
    with left:
        st.subheader("Investigation Setup")

        subreddits = st.text_input(
            "Subreddits (comma separated)",
            placeholder="Scams, IsThisAScamIndia, CryptoScams"
        )

        posts = st.slider(
            "Posts per Subreddit",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )

        time_range = st.selectbox(
            "Time Range",
            [
                "Latest",
                "Last 7 Days",
                "Last 30 Days",
                "Last 90 Days",
                "Last 1 Year"
            ]
        )

        start = st.button(" Start Investigation", use_container_width=True)
        if start:
            if not subreddits.strip():
                st.error("Please enter at least one subreddit.")
            else:
                subreddit_list = [item.strip() 
                                for item in 
                                subreddits.split(",") if item.strip()]
                st.session_state.screen = "progress"
                st.rerun()
    with right:
        st.subheader("System Status")

        st.success("🟢 OCR Engine Ready")

        st.success("🟢 AI Model Loaded")

        st.success("🟢 Browser Ready")

        st.success("🟢 Excel Export Ready")

        st.caption("Version 1.0")

if st.session_state.screen == "progress":

    st.title("🚀 Investigation Running")

    progress_bar = st.progress(0)

    st.info("Preparing investigation...")

    st.subheader("Investigation Steps")

    st.write("○ Reddit Collection")

    st.write("○ Image Download")

    st.write("○ OCR Extraction")

    st.write("○ Entity Extraction")

    st.write("○ AI Analysis")

    st.write("○ Screenshot")

    st.write("○ Excel Report")
