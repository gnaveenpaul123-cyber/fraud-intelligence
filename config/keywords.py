"""Cheap local signals used to avoid sending unrelated posts to the AI model."""

import re

# These terms intentionally cover several scam families.  They do not decide that a
# post is fraudulent; they only decide whether it is worth doing entity extraction.
fraud_keywords = [
    # General fraud language
    "scam", "fraud", "scammer", "fraudulent", "cheated", "cheating", "victim",
    "stolen", "lost money", "money taken", "phishing", "impersonation",
    "impersonating", "impersonated", "fake",
    "complaint", "report fraud", "cyber crime",
    # Payments and banking
    "upi", "phonepe", "paytm", "google pay", "gpay", "bhim", "qr code",
    "scan qr", "upi id", "upi pin", "bank account", "account number", "ifsc",
    "customer care", "refund", "payment failed", "transaction id",
    # Crypto
    "crypto", "bitcoin", "btc", "ethereum", "usdt", "wallet",
    "metamask", "binance", "coinbase", "seed phrase", "private key",
    "investment", "trading", "forex", "giveaway", "airdrop",
    # Employment and other common social-engineering scams
    "job scam", "fake job", "work from home", "recruiter", "registration fee",
    "task scam", "telegram", "whatsapp", "loan scam", "parcel", "courier",
    "otp", "verification code",
]


def is_fraud_related_keyword(text):
    """Stage 1: inexpensive broad scam-signal filter before any AI request."""
    text = text.lower()
    # Word boundaries prevent short terms such as "otp" or "btc" from matching
    # inside ordinary words, which would unnecessarily increase AI requests.
    return any(
        re.search(r"(?<!\\w)" + re.escape(keyword) + r"(?!\\w)", text)
        for keyword in fraud_keywords
    )


# Backwards-compatible name for callers outside the current pipeline.
is_upi_related_keyword = is_fraud_related_keyword
