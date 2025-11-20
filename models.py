# models.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import json

class Claim(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    verdict: Optional[str] = None
    credibility_score: Optional[int] = None
    summary: Optional[str] = None
    sources_json: Optional[str] = None   # list[dict] as JSON
    related_json: Optional[str] = None   # list[str] as JSON
    checked_at: datetime = Field(default_factory=datetime.utcnow)

    def set_sources(self, sources):
        self.sources_json = json.dumps(sources or [])

    def get_sources(self):
        if not self.sources_json:
            return []
        return json.loads(self.sources_json)

    def set_related(self, related):
        self.related_json = json.dumps(related or [])

    def get_related(self):
        if not self.related_json:
            return []
        return json.loads(self.related_json)
