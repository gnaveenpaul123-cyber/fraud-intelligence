import re

url_pattern = re.compile(r'https?://\S+')


def extract_entities(text):
    phones = re.findall(r'\b(?:\+91[- ]?)?[6-9]\d{9}\b', text)

    upi_ids = re.findall(r'[\w.\-]{2,}@[a-zA-Z]{2,}', text)

    emails = re.findall(
    r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
    text
    )

    urls = url_pattern.findall(text) 
    return {"phones" : phones,
            "upi_ids": upi_ids,
            "emails" : emails,
            "urls" : urls
            }