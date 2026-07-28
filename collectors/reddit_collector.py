import time
import re
from dotenv import load_dotenv
load_dotenv()
import feedparser
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

from config.settings import REDDIT_HEADERS
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



def fetch_reddit_post_data(permalink):
    """
    Fetch the full self-text of a post via Reddit's JSON API, since RSS summaries
    are often truncated. permalink is the post's reddit.com URL (post.link from RSS).
    Falls back to empty string on failure.
    """
    json_url = permalink.rstrip("/") + ".json"
    try:
        resp = requests.get(json_url, headers=REDDIT_HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        post_data = data[0]["data"]["children"][0]["data"]
        return post_data
    except Exception as e:
        print(f"Could not fetch full post text for {permalink}: {e}")
    
        return None



def clean_reddit_text(text):
    text = text.replace("[link]","")
    text =  text.replace("[comments]", "")
    text = re.sub(r"submitted by\s+/u/\S+", "",text)
    return text.strip()
