import os
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL_NAME = "llama-3.3-70b-versatile"
LAST_SEEN_FILE = "last_seen.json"

REDDIT_HEADERS = {
    "User-Agent": "upi-scam-research-script/1.0 (by u/your_reddit_username)"
}