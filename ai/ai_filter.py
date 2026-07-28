import time
import re
import json
import os
from dotenv import load_dotenv
load_dotenv()
import requests

from config.settings import (GROQ_API_KEY, 
GROQ_URL, 
MODEL_NAME)
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