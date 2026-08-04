import re

url_pattern = re.compile(r'https?://\S+')
account_number_pattern = re.compile(
    r"\b(?:bank\s*)?(?:account|a/c|acct)(?:\s*(?:number|no\.?))?\s*"
    r"(?:is\s*)?[:\-]?\s*([0-9][0-9\s-]{7,22}[0-9])\b",
    re.IGNORECASE,
)

# Common cryptocurrency address formats.  We retain only high-confidence formats
# to avoid treating arbitrary Reddit IDs as wallets.
ethereum_wallet_pattern = re.compile(r'\b0x[a-fA-F0-9]{40}\b')
bitcoin_wallet_pattern = re.compile(r'\b(?:bc1)[ac-hj-np-z02-9]{11,71}\b|\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b')
tron_wallet_pattern = re.compile(r'\bT[1-9A-HJ-NP-Za-km-z]{33}\b')
telegram_handle_pattern = re.compile(r'(?:https?://)?t\.me/([A-Za-z0-9_]{5,32})', re.IGNORECASE)
whatsapp_pattern = re.compile(r'(?:https?://)?(?:wa\.me|chat\.whatsapp\.com)/[^\s/?#]+', re.IGNORECASE)


def _unique(values):
    return list(dict.fromkeys(values))


def extract_entities(text):
    phones = _unique(re.findall(r'\b(?:\+91[- ]?)?[6-9]\d{9}\b', text))

    # UPI handles have no dot in the provider portion.  This prevents e-mail
    # addresses from being mistakenly displayed as UPI IDs.
    upi_ids = _unique(re.findall(
        r'(?<![\w.-])([\w.-]{2,}@[a-zA-Z][a-zA-Z0-9_-]{1,})(?![\w.-])', text
    ))

    account_numbers = []
    for match in account_number_pattern.findall(text):
        number = re.sub(r"[^0-9]", "", match)
        if 9 <= len(number) <= 18:
            account_numbers.append(number)

    emails = _unique(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text))

    wallet_addresses = _unique(
        ethereum_wallet_pattern.findall(text)
        + bitcoin_wallet_pattern.findall(text)
        + tron_wallet_pattern.findall(text)
    )
    contact_handles = _unique(
        [f"@{handle}" for handle in telegram_handle_pattern.findall(text)]
        + whatsapp_pattern.findall(text)
    )
    urls = _unique(url_pattern.findall(text))
    return {"phones" : phones,
            "upi_ids": upi_ids,
            "account_numbers": _unique(account_numbers),
            "emails" : emails,
            "wallet_addresses": wallet_addresses,
            "contact_handles": contact_handles,
            "urls" : urls,
            }
