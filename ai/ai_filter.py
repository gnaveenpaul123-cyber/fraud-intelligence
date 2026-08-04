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
def analyze_scam(combined_text):
    """Ask the model whether a UPI-ID-bearing post describes a UPI scam."""
    prompt = f"""
You are a fraud intelligence analyst.

Analyse the following Reddit post and extracted evidence.

Evidence:
{combined_text[:3000]}

Determine whether this describes a genuine UPI payment scam. Confirm it only when
the scam mechanism involves UPI (for example a fraudulent UPI ID, collect request,
QR code, or UPI PIN) and the supplied evidence contains a UPI ID.

Return ONLY valid JSON in this exact format:

{{
    "is_scam": true,
    "confidence": 94,
    "scam_type": "UPI Payment Scam",
    "summary": "Brief explanation in 2-4 sentences."
}}

Rules:

1. is_scam must be true or false.
2. confidence must be an integer from 0 to 100.
3. scam_type must be exactly "UPI Payment Scam" when is_scam is true, otherwise
   use "Unknown".
4. summary should be concise.
5. Return JSON only. No markdown. No extra text.
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 250,
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
            content = data["choices"][0]["message"]["content"].strip()

            try:
                result = json.loads(content)
                # Keep every caller (dashboard and standalone script) on the
                # single currently supported report category.
                result["scam_type"] = "UPI Payment Scam" if result.get("is_scam") else "Unknown"
                return result
            except json.JSONDecodeError:
                print("Invalid JSON returned by AI.")
                return {
                    "is_scam": False,
                    "confidence": 0,
                    "scam_type": "Unknown",
                    "summary": "AI returned an invalid response."
                    }
        except Exception as e:
            print(f"AI check error on attempt {attempt}: {e}")
            time.sleep(backoff * attempt)
    print("AI check failed after retries, defaulting to exclude.")
    return {
        "is_scam" : False,
        "confidence" : 0,
        "scam_type" : "unknown",
        "summary" : "AI request failed"
    }
