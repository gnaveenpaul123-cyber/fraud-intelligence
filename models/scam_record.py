from dataclasses import dataclass
from typing import List
@dataclass
class ScamRecord:
    subreddit : str
    title : str
    summary : str
    link : str
    phones : list[str]
    upi_ids : list[str]
    emails : list[str]
    urls: list[str]
    def to_dict(self):
        return {
            "subreddit": self.subreddit,
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "phones": self.phones,
            "upi_ids": self.upi_ids,
            "emails": self.emails,
            "urls": self.urls
        }