"""Cheap local signals used to avoid sending unrelated posts to the AI model."""

import re

# These terms are the first, cheap filter for UPI scam reports.  They do not decide
# that a post is fraudulent; they only decide whether it is worth extracting a UPI ID.
fraud_keywords = [
    # UPI payment methods and identifiers
    "upi", "phonepe", "paytm", "google pay", "gpay", "bhim", "qr code",
    "scan qr", "upi id", "upi pin", "payment request", "collect request",
    "customer care", "refund", "payment failed", "transaction id",

    # Non-UPI keywords retained for future expansion:
    # "scam", "fraud", "scammer", "fraudulent", "cheated", "cheating", "victim",
    # "stolen", "lost money", "money taken", "phishing", "impersonation",
    # "impersonating", "impersonated", "fake", "complaint", "report fraud", "cyber crime",
    # "bank account", "account number", "ifsc",
    # "crypto", "bitcoin", "btc", "ethereum", "usdt", "wallet",
    # "metamask", "binance", "coinbase", "seed phrase", "private key",
    # "investment", "trading", "forex", "giveaway", "airdrop",
    # "job scam", "fake job", "work from home", "recruiter", "registration fee",
    # "task scam", "telegram", "whatsapp", "loan scam", "parcel", "courier",
    # "otp", "verification code",
]

_fraud_keyword_pattern = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(keyword) for keyword in fraud_keywords) + r")(?!\w)",
    re.IGNORECASE,
)
# Catch UPI IDs even when the post does not spell out the word "UPI" (for example,
# "I paid scammer@okaxis").  The dot restriction avoids matching normal e-mails.
_upi_id_pattern = re.compile(r"(?<![\w.-])[\w.-]{2,}@[a-zA-Z][a-zA-Z0-9_-]{1,}(?![\w.-])")


def is_fraud_related_keyword(text):
    """Compatibility wrapper: Stage 1 now admits only UPI-related posts."""
    return is_upi_related_keyword(text)


def is_upi_related_keyword(text):
    """Stage 1: inexpensive UPI-only filter before fetching/OCR/AI work."""
    return bool(_fraud_keyword_pattern.search(text) or _upi_id_pattern.search(text))
