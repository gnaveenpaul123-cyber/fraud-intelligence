from dataclasses import dataclass
from typing import List
@dataclass
class ScamRecord:
    subreddit : str
    post_date: str
    title : str
    summary : str
    link : str
    phones : list[str]
    upi_ids : list[str]
    account_numbers : list[str]
    emails : list[str]
    urls: list[str]
    confidence : int
    scam_type : str
    ai_summary : str
    def to_dict(self):
        return {
            "subreddit": self.subreddit,
            "post_date": self.post_date,
            "title": self.title,
            "summary" : self.summary,
            "link": self.link,
            "phones": self.phones,
            "upi_ids": self.upi_ids,
            "account_numbers": self.account_numbers,
            "emails": self.emails,
            "urls": self.urls,
            "confidence" : self.confidence,
            "scam_type" : self.scam_type,
            "ai_summary" : self.ai_summary
        }
