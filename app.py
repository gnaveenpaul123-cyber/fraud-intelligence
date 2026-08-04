import os
import time

import streamlit as st

from worker import start_worker


st.set_page_config(
    page_title="Fraud Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
    .main .block-container { max-width: 1200px; padding-top: 2.5rem; }
    .task-complete { color: #16803c; font-weight: 600; }
    .task-active { color: #0f5fa7; font-weight: 600; }
    .task-pending { color: #7a7a7a; }
    </style>
    """,
    unsafe_allow_html=True,
)

TASKS = [
    "RSS Collection",
    "Image Download",
    "OCR Extraction",
    "Entity Extraction",
    "AI Analysis",
    "Screenshot Capture",
    "Saving",
    "Excel Report",
]


def initialise_session_state():
    defaults = {
        "screen": "setup",
        "investigation_started": False,
        "run_metrics": {},
        "run_records": [],
        "run_duration": 0,
        "run_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def format_duration(seconds):
    seconds = int(seconds or 0)
    return f"{seconds // 60}m {seconds % 60:02d}s"


def render_kpis(metrics):
    # Posts scanned is the single KPI reliably available throughout the run.
    st.metric("Posts Scanned", metrics.get("posts_scanned", 0))


def start_new_investigation():
    st.session_state.investigation_started = False
    st.session_state.run_metrics = {}
    st.session_state.run_records = []
    st.session_state.run_duration = 0
    st.session_state.run_error = None
    st.session_state.screen = "setup"


initialise_session_state()

if st.session_state.screen == "setup":
    st.title("fraudtraceAI")
    st.caption("Investigate scam reports on Reddit. Configure an investigation to begin.")
    render_kpis(st.session_state.run_metrics)

    left, right = st.columns([2, 1], gap="large")
    with left:
        st.subheader("Investigation Setup")
        with st.form("investigation_setup"):
            subreddits = st.text_input(
                "Subreddits (comma separated)",
                placeholder="Scams, IsThisAScamIndia, CryptoScams",
            )
            posts = st.slider(
                "Posts per Subreddit", min_value=10, max_value=200,
                value=50, step=10,
            )
            time_range = st.selectbox(
                "Time Range",
                ["Latest", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 1 Year"],
            )
            start = st.form_submit_button("Start Investigation", use_container_width=True)

        if start:
            if not subreddits.strip():
                st.error("Please enter at least one subreddit.")
            else:
                st.session_state.subreddit_list = [
                    item.strip() for item in subreddits.split(",") if item.strip()
                ]
                st.session_state.posts = posts
                st.session_state.time_range = time_range
                st.session_state.screen = "progress"
                st.rerun()

    with right:
        st.subheader("System Status")
        st.success("OCR Engine Ready")
        st.success("AI Model Loaded")
        st.success("Browser Evidence Ready")
        st.success("Excel Export Ready")
        st.caption("Version 1.0")

elif st.session_state.screen == "progress":
    st.title("Investigation Running")
    st.caption("Live status updates are shown as each post moves through the pipeline.")

    kpi_placeholder = st.empty()
    with kpi_placeholder.container():
        render_kpis({})

    progress_bar = st.progress(0, text="Preparing investigation...")
    detail_placeholder = st.empty()
    task_placeholder = st.empty()
    latest_metrics = {}
    completed_tasks = set()

    def render_tasks(active_stage=None):
        task_lines = []
        for task in TASKS:
            if task in completed_tasks:
                task_lines.append(f'<p class="task-complete">✓ {task}</p>')
            elif task == active_stage:
                task_lines.append(f'<p class="task-active">⏳ {task}</p>')
            else:
                task_lines.append(f'<p class="task-pending">○ {task}</p>')
        task_placeholder.markdown("".join(task_lines), unsafe_allow_html=True)

    def progress_callback(stage, percent, details=None):
        details = details or {}
        latest_metrics.clear()
        latest_metrics.update(details)
        active_stage = None if stage == "Complete" else stage
        if active_stage:
            completed_tasks.update(TASKS[:TASKS.index(active_stage)])
        elif stage == "Complete":
            completed_tasks.update(TASKS)
        render_tasks(active_stage)
        progress_bar.progress(percent, text=details.get("message", stage))
        with kpi_placeholder.container():
            render_kpis(details)

        subreddit = details.get("subreddit", "—")
        current_post = details.get("current_post", 0)
        total_posts = details.get("total_posts", 0)
        error_count = details.get("errors", 0)
        detail_placeholder.info(
            f"Current subreddit: r/{subreddit}  |  Post: {current_post}/{total_posts}  |  "
            f"Stage: {stage}  |  Recoverable errors: {error_count}"
        )

    render_tasks()
    if not st.session_state.investigation_started:
        st.session_state.investigation_started = True
        started_at = time.monotonic()
        try:
            records = start_worker(
                st.session_state.subreddit_list,
                st.session_state.posts,
                st.session_state.time_range,
                progress_callback=progress_callback,
            )
            st.session_state.run_records = [record.to_dict() for record in records]
            st.session_state.run_metrics = latest_metrics
            st.session_state.run_duration = latest_metrics.get(
                "duration_seconds", time.monotonic() - started_at,
            )
            st.session_state.screen = "results"
            st.rerun()
        except Exception as error:
            st.session_state.run_error = str(error)
            st.session_state.run_metrics = latest_metrics
            st.error("The investigation could not complete. Review logs/investigation.log for details.")

elif st.session_state.screen == "results":
    metrics = st.session_state.run_metrics
    st.title("Investigation Results")
    st.caption(f"Completed in {format_duration(st.session_state.run_duration)}")
    records = st.session_state.run_records
    if records:
        st.subheader("Confirmed scam reports")
        header = st.columns([1.1, 1.5, 1.5, 1.5, 1.2, 0.8])
        for column, label in zip(header, ["Date of Post", "UPI ID", "Phone Number", "Account Number", "Scam Type", ""]):
            column.markdown(f"**{label}**")

        for index, record in enumerate(records):
            row = st.columns([1.1, 1.5, 1.5, 1.5, 1.2, 0.8])
            row[0].write(record.get("post_date", "Unavailable"))
            row[1].write(", ".join(record.get("upi_ids", [])) or "—")
            row[2].write(", ".join(record.get("phones", [])) or "—")
            row[3].write(", ".join(record.get("account_numbers", [])) or "—")
            row[4].write(record.get("scam_type", "Unknown"))
            if row[5].button("View", key=f"view_record_{index}"):
                st.session_state.selected_record = record
                st.session_state.screen = "details"
                st.rerun()
    else:
        st.info("No confirmed scam reports with UPI IDs, phone numbers, or account numbers were found.")

    report_path = "reddit_scam_report.xlsx"
    if os.path.exists(report_path):
        with open(report_path, "rb") as report_file:
            st.download_button(
                "Download Excel Report", data=report_file.read(), file_name=report_path,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    st.button("Start New Investigation", on_click=start_new_investigation)

elif st.session_state.screen == "details":
    record = st.session_state.get("selected_record")
    if not record:
        st.session_state.screen = "results"
        st.rerun()

    st.title("Full Extraction")
    st.caption(f"Post date: {record.get('post_date', 'Unavailable')}")
    st.subheader(record.get("title", "Untitled post"))
    st.write(record.get("summary", "No summary was extracted."))
    st.markdown(f"**Scam type:** {record.get('scam_type', 'Unknown')}")
    st.markdown(f"**AI confidence:** {record.get('confidence', 0)}%")
    st.markdown(f"**Source link:** {record.get('link', '')}")
    if record.get("ai_summary"):
        st.markdown(f"**AI summary:** {record['ai_summary']}")
    st.button("Back to results", on_click=lambda: st.session_state.update(screen="results"))
