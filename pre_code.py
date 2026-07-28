import time
import re
import json
import os
from dotenv import load_dotenv
load_dotenv()
import feedparser
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

#Groq config 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL_NAME = "llama-3.3-70b-versatile"

url_pattern = re.compile(r'https?://\S+')

LAST_SEEN_FILE = "last_seen.json"
# To avoid duplicates in future and reduce burining of more APIs
def load_last_seen():
    """Loads {subreddit: last_seen_fullname} from disk. Returns {} if the file doesn't exist yet."""
    if not os.path.exists(LAST_SEEN_FILE):
        return {}
    try:
        with open(LAST_SEEN_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not read {LAST_SEEN_FILE}, starting fresh: {e}")
        return {}

def save_last_seen(last_seen):
    """Saves {subreddit: last_seen_fullname} to disk."""
    try:
        with open(LAST_SEEN_FILE, "w") as f:
            json.dump(last_seen, f, indent=2)
    except Exception as e:
        print(f"Could not save {LAST_SEEN_FILE}: {e}")

# keywords to look into the posts relates to india
upi_keywords = [
    "upi",
    "phonepe",
    "paytm",
    "google pay",
    "gpay",
    "bhim",
    "qr code",
    "scan qr",
    "upi id",
    "upi pin"
]

def is_upi_related_keyword(text):
    """Stage 1: cheap substring check — casts a wide net, lets false positives through."""
    text = text.lower()
    return any(keyword in text for keyword in upi_keywords)
#defining the prompt to GROQ. 
def is_upi_scam_ai(title, summary):
    """Stage 2: ask the model (via Groq) whether this is an actual UPI payment scam."""
    prompt = f"""You are filtering Reddit posts for a UPI (India payment app) scam report.
Only genuine, first-hand incident reports should be kept.
Post title: {title}
Post content: {summary[:1500]}
Answer YES only if ALL of these are true:
1. The post describes a SPECIFIC incident that happened to the poster or someone \
they know personally (not a hypothetical, not general advice, not a news/blog \
roundup of "common scams").
2. The scam mechanism specifically involves UPI, PhonePe, GPay, BHIM, or a UPI \
QR code — e.g. being tricked into scanning a QR code, sharing a UPI PIN, sending \
money to a fake UPI ID, or receiving a fraudulent payment request via one of \
these apps.
3. There is a DISTINCT BAD-FAITH ACTOR — a scammer, fraudster, or con artist who \
deliberately deceived or manipulated the poster. A bank, payment app, or technical \
glitch is NOT a bad-faith actor.
Answer NO for any of these cases:
- General "here are the top N UPI scams" articles, blog posts, or educational lists
- Posts only asking which UPI app is best, reviewing an app, or app bugs/complaints
- The poster's own mistake (e.g. sent money to the wrong UPI ID by accident) with \
no scammer/fraud involved
- UPI mentioned only in passing while the actual scam involved a different method \
(cash, card, bank transfer, crypto) with no UPI element
- Posts about frozen/blocked bank accounts, KYC issues, or transaction failures \
with no scam described
- Technical glitches, double-charges, delayed refunds, failed transactions, or \
bank/app customer-service disputes where no scammer tricked anyone — even if the \
poster lost money or is frustrated, this is NOT a scam without a deceiving third party
- Receiving money unexpectedly is only a scam if the post describes being asked to \
send it back, being pressured, or being accused of fraud as part of a mule scheme \
— not just "I got money from someone I don't know, is this a scam?" with nothing else
Answer with exactly one word: YES or NO."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 5,
        "temperature": 0
    }
    max_retries = 5 #retrying to load the posts in order to get the posts
    backoff = 5 
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(GROQ_URL, headers=headers, data=json.dumps(payload), timeout=30)
            if resp.status_code == 429:
                wait = backoff * attempt
                print(f"Rate limited (429). Waiting {wait}s before retry {attempt}/{max_retries}...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            answer = data["choices"][0]["message"]["content"].strip().upper()
            return answer.startswith("YES")
        except Exception as e:
            print(f"AI check error on attempt {attempt}: {e}")
            time.sleep(backoff * attempt)
    print("AI check failed after retries, defaulting to exclude.")
    return False

# Subreddits to monitor (r/fraud removed — subreddit no longer exists, returns 404)
subreddits = [
    "IsThisAScamIndia"
]

REDDIT_HEADERS = {
    "User-Agent": "upi-scam-research-script/1.0 (by u/your_reddit_username)"
}

def fetch_full_post_text(permalink):
    """
    Fetch the full self-text of a post via Reddit's JSON API, since RSS summaries
    are often truncated. permalink is the post's reddit.com URL (post.link from RSS).
    Falls back to empty string on failure.
    """
    json_url = permalink.rstrip("/") + ".json"
    try:
        resp = requests.get(json_url, headers=REDDIT_HEADERS, timeout=15)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        post_data = data[0]["data"]["children"][0]["data"]
        return post_data.get("selftext", "") or ""
    except Exception as e:
        print(f"Could not fetch full post text for {permalink}: {e}")
        return ""

def fetch_reddit_rss_paginated(subreddit, max_pages=5, per_page_count=25, stop_at_fullname=None):
    """
    Fetch multiple pages of a subreddit's RSS feed using Reddit's 'after' pagination.
    Reddit RSS entry IDs are fullnames (e.g. t3_abc123) — pass the last one as 'after'
    to get the next page. Stops early if a page returns no entries or no further 'after'.

    NEW: if stop_at_fullname is given (the last post fullname processed on a previous
    run), pagination stops as soon as that fullname is seen, and only entries newer
    than it are returned. This is what prevents re-processing (and re-billing the AI
    for) posts you've already handled in an earlier run.
    """
    all_entries = []
    after = None
    for page in range(1, max_pages + 1):
        rss_url = f"https://www.reddit.com/r/{subreddit}/.rss?limit={per_page_count}"
        if after:
            rss_url += f"&after={after}&count={per_page_count * (page - 1)}"
        status_code = None
        feed = None
        for attempt in range(1, 4):#attempt to load the posts
            try:
                resp = requests.get(rss_url, headers=REDDIT_HEADERS, timeout=15)
                status_code = resp.status_code
                if status_code == 429:
                    wait = 20 * attempt
                    print(f"Reddit rate limited on r/{subreddit} page {page}. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                feed = feedparser.parse(resp.content)
                break
            except Exception as e:
                print(f"Failed to fetch r/{subreddit} page {page} (attempt {attempt}): {e}")
                time.sleep(10)
        if feed is None or not feed.entries:
            print(f"r/{subreddit} page {page}: no entries, stopping pagination.")
            break
        print(f"r/{subreddit} page {page}: {len(feed.entries)} posts (status {status_code})")

 
        reached_stop_point = False
        for entry in feed.entries:
            entry_id = entry.get("id", "")
            if stop_at_fullname and entry_id == stop_at_fullname:
                reached_stop_point = True
                break
            all_entries.append(entry)

        if reached_stop_point:
            print(f"r/{subreddit}: reached previously-seen post, stopping pagination early.")
            break

        
        last_id = feed.entries[-1].get("id", "")
        if "t3_" in last_id:
            after = last_id[last_id.index("t3_"):]
        else:
            print(f"Could not extract fullname for pagination on r/{subreddit}, stopping.")
            break
        if len(feed.entries) < per_page_count:
            
            break
        time.sleep(5)  # small pause between pages of the same subreddit
    return all_entries

# Create Excel workbook
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

# Summary worksheet — numbers only, no post content
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

last_seen = load_last_seen()

seen_links = set()
for subreddit in subreddits:
    print(f"\nChecking r/{subreddit}")

    stop_at_fullname = last_seen.get(subreddit) 
    entries = fetch_reddit_rss_paginated(
        subreddit, max_pages=7, per_page_count=25, stop_at_fullname=stop_at_fullname
    )
    print(f"Total NEW posts collected since last run: {len(entries)}")

    
    total_fetched = len(entries)
    passed_keyword = 0
    passed_ai = 0
    final_with_contact_info = 0

    
    newest_fullname_this_run = entries[0].get("id", "") if entries else None

    for post in entries:
        if post.link in seen_links:
            continue
        seen_links.add(post.link)

        summary = BeautifulSoup(post.summary, "html.parser").get_text()
        text = (post.title + " " + summary).lower()

        # --- Stage 1: keyword filter (cheap, uses RSS summary only) ---
        if not is_upi_related_keyword(text):
            continue
        passed_keyword += 1

        # Post passed Stage 1 — fetch the full post body 
        full_text = fetch_full_post_text(post.link)
        if full_text:
            summary = full_text  # use full body for AI check and regex extraction
            text = (post.title + " " + summary).lower()
        time.sleep(2)  

        # Stage 2: AI verification ---
        if not is_upi_scam_ai(post.title, summary):
            print(f"Skipped (AI ruled not a UPI scam): {post.title}")
            continue
        passed_ai += 1

        phones = re.findall(r'\b(?:\+91[- ]?)?[6-9]\d{9}\b', text)
        upi_ids = re.findall(r'[\w.\-]{2,}@[a-zA-Z]{2,}', text)
        emails = re.findall(
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
            text
        )
        urls = url_pattern.findall(text)

        if phones or upi_ids:
            final_with_contact_info += 1

        print("=" * 80)
        print("TITLE:", post.title)
        print("SUMMARY:", summary[:500])
        print("LINK:", post.link)
        print("URLs found:", urls)
        # appending the info into workbook
        ws.append([
            subreddit,
            summary[:500],
            ", ".join(phones),
            ", ".join(upi_ids),
            ", ".join(emails),
            post.link
        ])

        time.sleep(3)  # pause between AI calls to stay under rate limits

    # addidng the numbers to worksheet
    summary_ws.append([
        subreddit,
        total_fetched,
        total_fetched - passed_keyword,
        passed_keyword,
        passed_keyword - passed_ai,
        passed_ai,
        final_with_contact_info
    ])

    
    if newest_fullname_this_run:
        last_seen[subreddit] = newest_fullname_this_run

    time.sleep(30)  


save_last_seen(last_seen)

wb.save("reddit_upi_scams.xlsx")
print("\n✅ reddit_upi_scams.xlsx created successfully (with Summary sheet)!")
