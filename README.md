# ArXiv Monitor - Setup Instructions

## Installation

1. **Install dependencies:**
```bash
./install.sh
```

2. **Run the application:**
```bash
python main.py
```

Or directly with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

3. **Access the application:**
Open your browser and navigate to `http://localhost:8001`

## Features

### 🎯 Core Functionality
- **Automatic Monitoring**: Fetches new papers every hour from selected arXiv categories
- **Real-time Dashboard**: Clean, modern UI showing latest papers with metadata
- **Smart Tracking**: Automatically tracks which papers you've already seen
- **Category Filtering**: Support for multiple arXiv categories (cs.CV, cs.LG, cs.AI, etc.)

### 📊 Dashboard Features
- **Paper Cards**: Display title, abstract, authors, publication date
- **New Paper Indicators**: Visual badges for papers you haven't seen yet
- **Quick Links**: Direct links to arXiv page and PDF for each paper
- **Category Tags**: See which categories each paper belongs to
- **Expandable Abstracts**: Click to expand/collapse long abstracts

### 🔧 Controls
- **Manual Fetch**: Trigger immediate paper fetch with one click
- **Mark All as Seen**: Clear all "new" badges at once
- **Auto-fetch Toggle**: Pause/resume automatic hourly fetching
- **Clear Data**: Reset all stored papers and seen status

## API Endpoints

The FastAPI backend provides these endpoints:

- `GET /` - Web interface
- `GET /api/papers` - Get all stored papers
- `POST /api/fetch` - Manually trigger paper fetching
- `GET /api/status` - Get current fetch status
- `POST /api/mark-all-seen` - Mark all papers as seen
- `POST /api/toggle-auto-fetch` - Toggle automatic fetching
- `GET /api/config` - Get category configuration
- `POST /api/config` - Update category configuration
- `POST /api/clear` - Clear all data

## Data Storage

The application stores data locally in the `./arxiv_data/` directory:
- `papers.json` - All fetched papers
- `seen_ids.json` - IDs of papers you've seen
- `config.json` - Category configuration
- `status.json` - Last fetch status

## Customization

### Change Categories
Modify the default categories in the `DataStorage.load_config()` method:

```python
return [
    CategoryConfig(category="cs.CV", enabled=True),    # Computer Vision
    CategoryConfig(category="cs.LG", enabled=True),    # Machine Learning
    CategoryConfig(category="cs.AI", enabled=True),    # Artificial Intelligence
    CategoryConfig(category="cs.CL", enabled=True),    # Computation and Language
    # Add more categories as needed
]
```

### Change Fetch Interval
Modify the fetch interval in the lifespan function:

```python
app.state.fetch_interval = 3600  # seconds (default: 1 hour)
```

### Available arXiv Categories
Some popular CS categories:
- `cs.CV` - Computer Vision and Pattern Recognition
- `cs.LG` - Machine Learning
- `cs.AI` - Artificial Intelligence
- `cs.CL` - Computation and Language
- `cs.NE` - Neural and Evolutionary Computing
- `cs.RO` - Robotics
- `cs.IR` - Information Retrieval
- `cs.HC` - Human-Computer Interaction

## Integration with Claude API

To integrate with Claude API for paper analysis:

1. **Install Anthropic SDK:**
```bash
pip install anthropic
```

2. **Create an analysis script** (`analyze_paper.py`):
```python
import anthropic
import json
from pathlib import Path

client = anthropic.Anthropic(api_key="your-api-key-here")

def analyze_paper(paper_id):
    # Load paper data
    data_path = Path("./arxiv_data/papers.json")
    with open(data_path, 'r') as f:
        papers = json.load(f)
    
    paper = papers.get(paper_id)
    if not paper:
        print(f"Paper {paper_id} not found")
        return
    
    # Create prompt for Claude
    prompt = f"""
    Please analyze this research paper:
    
    Title: {paper['title']}
    Abstract: {paper['abstract']}
    Categories: {', '.join(paper['categories'])}
    
    Provide:
    1. A brief summary (2-3 sentences)
    2. Key contributions
    3. Potential applications
    4. Suggested implementation approach
    """
    
    # Call Claude API
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    print(response.content[0].text)
    return response.content[0].text

# Example usage
if __name__ == "__main__":
    paper_id = input("Enter paper ID to analyze: ")
    analyze_paper(paper_id)
```

3. **Add to web interface** (optional):
You can extend the web interface to include an "Analyze" button that triggers the Claude API analysis.

## Troubleshooting

### Connection Issues
- Ensure you have an active internet connection
- Check if arXiv API is accessible: `http://export.arxiv.org/api/query`

### No Papers Showing
- Click "Fetch Now" to manually trigger fetching
- Check the browser console for errors
- Verify categories are correctly configured

### Data Persistence
- Papers are stored locally in `./arxiv_data/`
- Back up this directory to preserve your data

## Future Enhancements

Consider adding:
- Email notifications for papers matching specific keywords
- Export to BibTeX/CSV
- Advanced filtering (by date, author, keywords)
- Paper collections/favorites
- Integration with reference managers
- Batch processing with Claude API
- RSS feed generation

## License

This is a personal project for research paper monitoring. 