import os
import time

import streamlit as st

from worker import start_worker


st.set_page_config(
    page_title="reddit-fraudtraceai",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none; }
    .main .block-container { max-width: 1200px; padding-top: 2.5rem; }
    .task-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.75rem;
      margin-top: 1rem;
    }
    .task-card {
      min-height: 5.5rem;
      padding: 0.9rem 1rem;
      border: 1px solid #d9e2ec;
      border-radius: 0.6rem;
      background: #ffffff;
    }
    .task-card strong { display: block; margin-bottom: 0.4rem; }
    .task-complete { border-color: #86d5a4; background: #f0fdf4; }
    .task-complete .task-state { color: #16803c; font-weight: 600; }
    .task-active { border-color: #8dbce8; background: #eff6ff; }
    .task-active .task-state { color: #0f5fa7; font-weight: 600; }
    .task-pending { color: #687386; }
    .loader { display: inline-block; width: 0.8rem; height: 0.8rem; margin-right: 0.35rem;
      border: 2px solid #a9cce8; border-top-color: #0f5fa7; border-radius: 50%;
      vertical-align: -0.1rem; animation: fraudtrace-spin 0.75s linear infinite; }
    @keyframes fraudtrace-spin { to { transform: rotate(360deg); } }
    @media (max-width: 800px) {
      .task-grid { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

TASKS = [
    "RSS Collection",
    "Keyword Filter",
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
    scanned = metrics.get("posts_scanned", 0)
    useful = metrics.get("contact_information", 0)
    cards = st.columns(5)
    cards[0].metric("Posts Scanned", scanned)
    cards[1].metric("Filtered by Keywords", metrics.get("keyword_filtered_out", 0))
    cards[2].metric("Passed Keyword Screen", metrics.get("keyword_matches", 0))
    cards[3].metric("Contact Info Extracted", metrics.get("contact_info_found", 0))
    cards[4].metric("AI Confirmed", useful)


def render_subreddit_chart(metrics):
    """Show pipeline counts per subreddit with subreddits on the x-axis."""
    subreddit_stats = metrics.get("subreddit_stats", {})
    chart_data = [
        {
            "Subreddit": f"r/{subreddit}",
            "Posts with important information": counts.get("important_info_found", 0),
            "AI-confirmed posts": counts.get("ai_confirmed", 0),
        }
        for subreddit, counts in subreddit_stats.items()
    ]

    st.subheader("AI filter results by subreddit")
    st.caption("Posts with important information are sent to AI. Important information includes UPI IDs, phone numbers, account numbers, wallets, emails, and contact handles.")
    if not chart_data:
        st.info("No subreddit data is available for this investigation.")
        return

    st.bar_chart(
        chart_data,
        x="Subreddit",
        y=["Posts with important information", "AI-confirmed posts"],
        x_label="Subreddit",
        y_label="Number of posts",
        color=["#2563eb", "#16a34a"],
    )


def start_new_investigation():
    st.session_state.investigation_started = False
    st.session_state.run_metrics = {}
    st.session_state.run_records = []
    st.session_state.run_duration = 0
    st.session_state.run_error = None
    st.session_state.screen = "setup"


initialise_session_state()

if st.session_state.screen == "setup":
    st.title("reddit-fraudtraceai")
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
    st.title("reddit-fraudtraceai")
    st.subheader("Investigation running")
    st.caption("Live status updates are shown as each post moves through the pipeline.")

    kpi_placeholder = st.empty()
    with kpi_placeholder.container():
        render_kpis({})

    progress_bar = st.progress(0, text="Preparing investigation...")
    detail_placeholder = st.empty()
    task_placeholder = st.empty()
    latest_metrics = {}
    completed_tasks = set()
    active_task = [None]

    def render_tasks(active_stage=None):
        task_lines = []
        for task in TASKS:
            if task in completed_tasks:
                task_lines.append(
                    f'<div class="task-card task-complete"><strong>{task}</strong>'
                    '<span class="task-state">✓ Complete</span></div>'
                )
            elif task == active_stage:
                task_lines.append(
                    f'<div class="task-card task-active"><strong>{task}</strong>'
                    '<span class="task-state"><span class="loader"></span>In progress</span></div>'
                )
            else:
                task_lines.append(
                    f'<div class="task-card task-pending"><strong>{task}</strong>'
                    '<span class="task-state">○ Waiting</span></div>'
                )
        task_placeholder.markdown(
            f'<div class="task-grid">{"".join(task_lines)}</div>',
            unsafe_allow_html=True,
        )

    def progress_callback(stage, percent, details=None):
        details = details or {}
        latest_metrics.clear()
        latest_metrics.update(details)
        if stage == "Complete":
            completed_tasks.update(TASKS)
            active_task[0] = None
        elif stage in TASKS:
            if active_task[0] and active_task[0] != stage:
                completed_tasks.add(active_task[0])
            active_task[0] = stage
        render_tasks(active_task[0])
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
    st.title("reddit-fraudtraceai")
    st.subheader("Investigation results")
    st.caption(f"Completed in {format_duration(st.session_state.run_duration)}")
    records = st.session_state.run_records
    render_kpis(metrics)
    render_subreddit_chart(metrics)
    st.divider()
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
    st.subheader("Extracted information")
    evidence = {
        "UPI IDs": record.get("upi_ids", []),
        "Phone numbers": record.get("phones", []),
        "Account numbers": record.get("account_numbers", []),
        "Crypto wallet addresses": record.get("wallet_addresses", []),
        "Email addresses": record.get("emails", []),
        "Telegram / WhatsApp contacts": record.get("contact_handles", []),
    }
    for label, values in evidence.items():
        if values:
            st.markdown(f"**{label}:** {', '.join(values)}")
    if record.get("ai_summary"):
        st.markdown(f"**AI summary:** {record['ai_summary']}")
    st.button("Back to results", on_click=lambda: st.session_state.update(screen="results"))
