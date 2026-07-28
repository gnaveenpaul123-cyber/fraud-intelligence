from openpyxl import Workbook
def create_workbook():
    wb = Workbook()
    ws = wb.active
    ws.title = "Reddit UPI Scam Data"
    ws.append([
        "Subreddit",
        "Summary",
        "Phone Numbers",
        "UPI IDs",
        "Email",
        "Link"
    ])


    summary_ws = wb.create_sheet("Summary")
    summary_ws.append([
        "Subreddit",
        "Total Posts Fetched",
        "Rejected by Keyword Filter",
        "Passed Keyword Filter",
        "Rejected by AI",
        "Passed AI Verification",
        "Final Extracted"
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