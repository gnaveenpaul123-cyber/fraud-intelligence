from openpyxl import Workbook

def create_workbook():
    wb = Workbook()

    # Main Report Sheet
    ws = wb.active
    ws.title = "Scam Reports"

    ws.append([
        "Date",
        "Time",
        "Subreddit",
        "Post ID",
        "Title",
        "UPI IDs",
        "Phone Numbers",
        "Scam Type",
        "AI Confidence",
        "Evidence Folder",
        "Reddit URL"
    ])

    # Summary Sheet
    summary_ws = wb.create_sheet("Summary")

    summary_ws.append([
        "Subreddit",
        "RSS Fetched",
        "Failed Keyword",
        "Passed Keyword",
        "No Contact Info",
        "Sent To AI",
        "AI Rejected",
        "Final Cases"
    ])

    return wb, ws, summary_ws
  
def write_post(ws, record):
    ws.append([
        record.subreddit,
        record.summary[:500],
        ", ".join(record.phones),
        ", ".join(record.upi_ids),
        ", ".join(record.emails),
        record.link
    ])   

def write_summary(
    summary_ws,
    subreddit,
    total_fetched,
    passed_keyword,
    passed_ai,
    final_with_contact_info
):
    summary_ws.append([
        subreddit,
        total_fetched,
        total_fetched - passed_keyword,
        passed_keyword,
        passed_keyword - passed_ai,
        passed_ai,
        final_with_contact_info
    ])

def save_workbook(wb, filename):
    wb.save(filename)