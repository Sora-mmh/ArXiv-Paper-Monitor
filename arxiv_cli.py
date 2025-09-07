from fastapi import HTTPException
from typing import List
from datetime import datetime
import aiohttp
import xml.etree.ElementTree as ET
import re

from config import Paper


# ArXiv API client
class ArXivClient:
    BASE_URL = "http://export.arxiv.org/api/query"

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text from arXiv API"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    async def fetch_papers(category: str, max_results: int = 50) -> List[Paper]:
        """Fetch recent papers from a specific category"""
        params = {
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "lastUpdatedDate",
            "sortOrder": "descending",
        }

        papers = []
        async with aiohttp.ClientSession() as session:
            async with session.get(ArXivClient.BASE_URL, params=params) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"ArXiv API error: {response.status}",
                    )

                content = await response.text()
                root = ET.fromstring(content)

                # Parse XML namespace
                ns = {
                    "atom": "http://www.w3.org/2005/Atom",
                    "arxiv": "http://arxiv.org/schemas/atom",
                }

                entries = root.findall("atom:entry", ns)

                for entry in entries:
                    # Extract paper ID
                    id_text = entry.find("atom:id", ns).text
                    paper_id = id_text.split("/abs/")[-1]

                    # Extract title
                    title = ArXivClient.clean_text(entry.find("atom:title", ns).text)

                    # Extract abstract
                    abstract = ArXivClient.clean_text(
                        entry.find("atom:summary", ns).text
                    )

                    # Extract authors
                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name = author.find("atom:name", ns).text
                        if name:
                            authors.append(name)

                    # Extract categories
                    categories = []
                    for cat in entry.findall("atom:category", ns):
                        term = cat.get("term")
                        if term:
                            categories.append(term)

                    # Extract dates
                    published = datetime.fromisoformat(
                        entry.find("atom:published", ns).text.replace("Z", "+00:00")
                    )
                    updated = datetime.fromisoformat(
                        entry.find("atom:updated", ns).text.replace("Z", "+00:00")
                    )

                    # Generate URLs
                    arxiv_url = f"https://arxiv.org/abs/{paper_id}"
                    pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

                    paper = Paper(
                        id=paper_id,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        categories=categories,
                        published=published,
                        updated=updated,
                        arxiv_url=arxiv_url,
                        pdf_url=pdf_url,
                        fetched_at=datetime.utcnow(),
                        is_new=True,
                    )
                    papers.append(paper)

        return papers
