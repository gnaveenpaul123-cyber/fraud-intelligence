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