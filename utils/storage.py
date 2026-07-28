
import json
import os

from bs4 import BeautifulSoup
from config.settings import LAST_SEEN_FILE
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