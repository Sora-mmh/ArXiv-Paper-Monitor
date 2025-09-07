from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class Paper(BaseModel):
    id: str
    title: str
    abstract: str
    authors: List[str]
    categories: List[str]
    published: datetime
    updated: datetime
    arxiv_url: str
    pdf_url: str
    fetched_at: datetime
    is_new: bool = True

class CategoryConfig(BaseModel):
    category: str
    enabled: bool = True
    max_results: int = 50

class FetchStatus(BaseModel):
    last_fetch: Optional[datetime]
    papers_found: int
    new_papers: int
    status: str
    message: str = ""
