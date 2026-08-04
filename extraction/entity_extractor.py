import re

url_pattern = re.compile(r'https?://\S+')
account_number_pattern = re.compile(
    r"\b(?:bank\s*)?(?:account|a/c|acct)(?:\s*(?:number|no\.?))?\s*"
    r"(?:is\s*)?[:\-]?\s*([0-9][0-9\s-]{7,22}[0-9])\b",
    re.IGNORECASE,
)


def _unique(values):
    return list(dict.fromkeys(values))


def extract_entities(text):
    phones = _unique(re.findall(r'\b(?:\+91[- ]?)?[6-9]\d{9}\b', text))

    upi_ids = _unique(re.findall(r'[\w.\-]{2,}@[a-zA-Z]{2,}', text))

    account_numbers = []
    for match in account_number_pattern.findall(text):
        number = re.sub(r"[^0-9]", "", match)
        if 9 <= len(number) <= 18:
            account_numbers.append(number)

    emails = re.findall(
    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
    text
    )

    urls = url_pattern.findall(text) 
    return {"phones" : phones,
            "upi_ids": upi_ids,
            "account_numbers": _unique(account_numbers),
            "emails" : emails,
            "urls" : urls
            }
