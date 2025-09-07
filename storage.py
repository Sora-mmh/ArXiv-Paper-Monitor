from typing import List, Optional, Dict, Set
import json
from pathlib import Path

from config import Paper, CategoryConfig, FetchStatus


# Storage class for persistent data
class DataStorage:
    def __init__(self, base_dir: str = "./arxiv_data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.papers_file = self.base_dir / "papers.json"
        self.seen_file = self.base_dir / "seen_ids.json"
        self.config_file = self.base_dir / "config.json"
        self.status_file = self.base_dir / "status.json"
        
    def load_papers(self) -> Dict[str, Paper]:
        if self.papers_file.exists():
            with open(self.papers_file, 'r') as f:
                data = json.load(f)
                return {k: Paper(**v) for k, v in data.items()}
        return {}
    
    def save_papers(self, papers: Dict[str, Paper]):
        with open(self.papers_file, 'w') as f:
            data = {k: v.dict() for k, v in papers.items()}
            json.dump(data, f, default=str, indent=2)
    
    def load_seen_ids(self) -> Set[str]:
        if self.seen_file.exists():
            with open(self.seen_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_seen_ids(self, seen_ids: Set[str]):
        with open(self.seen_file, 'w') as f:
            json.dump(list(seen_ids), f)
    
    def load_config(self) -> List[CategoryConfig]:
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                return [CategoryConfig(**item) for item in data]
        # Default categories
        return [
            CategoryConfig(category="cs.CV", enabled=True),
            CategoryConfig(category="cs.LG", enabled=True),
            CategoryConfig(category="cs.AI", enabled=True),
        ]
    
    def save_config(self, config: List[CategoryConfig]):
        with open(self.config_file, 'w') as f:
            json.dump([c.dict() for c in config], f, indent=2)
    
    def load_status(self) -> Optional[FetchStatus]:
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                data = json.load(f)
                return FetchStatus(**data)
        return None
    
    def save_status(self, status: FetchStatus):
        with open(self.status_file, 'w') as f:
            json.dump(status.dict(), f, default=str, indent=2)