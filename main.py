from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from arxiv_cli import ArXivClient
from config import CategoryConfig, FetchStatus, Paper
from storage import DataStorage


# Background task for periodic fetching
async def periodic_fetch(app_state):
    """Background task to periodically fetch new papers"""
    while app_state["auto_fetch_enabled"]:
        try:
            # Fetch papers for all enabled categories
            all_papers = []
            config = app_state["storage"].load_config()

            for cat_config in config:
                if cat_config.enabled:
                    papers = await ArXivClient.fetch_papers(
                        cat_config.category, cat_config.max_results
                    )
                    all_papers.extend(papers)

            # Update storage
            seen_ids = app_state["storage"].load_seen_ids()
            existing_papers = app_state["storage"].load_papers()

            new_count = 0
            for paper in all_papers:
                if paper.id not in seen_ids:
                    paper.is_new = True
                    new_count += 1
                    seen_ids.add(paper.id)
                else:
                    paper.is_new = False
                existing_papers[paper.id] = paper

            app_state["storage"].save_papers(existing_papers)
            app_state["storage"].save_seen_ids(seen_ids)

            # Update status
            status = FetchStatus(
                last_fetch=datetime.utcnow(),
                papers_found=len(all_papers),
                new_papers=new_count,
                status="success",
                message=f"Fetched {len(all_papers)} papers, {new_count} new",
            )
            app_state["storage"].save_status(status)

        except Exception as e:
            status = FetchStatus(
                last_fetch=datetime.utcnow(),
                papers_found=0,
                new_papers=0,
                status="error",
                message=str(e),
            )
            app_state["storage"].save_status(status)

        # Wait for the specified interval (default: 1 hour)
        await asyncio.sleep(app_state["fetch_interval"])


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.storage = DataStorage()
    app.state.auto_fetch_enabled = True
    app.state.fetch_interval = 3600  # 1 hour in seconds
    app.state.fetch_task = None

    # Start background task
    app.state.fetch_task = asyncio.create_task(periodic_fetch(app.state.__dict__))

    yield

    # Shutdown
    app.state.auto_fetch_enabled = False
    if app.state.fetch_task:
        app.state.fetch_task.cancel()
        try:
            await app.state.fetch_task
        except asyncio.CancelledError:
            pass


# Create FastAPI app
app = FastAPI(
    title="ArXiv Paper Monitor",
    description="Lightweight arXiv paper monitoring system",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routes
@app.get("/")
async def root():
    """Serve the web interface"""
    # Read HTML file
    with open("templates/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/api/papers", response_model=List[Paper])
async def get_papers():
    """Get all stored papers"""
    papers = app.state.storage.load_papers()
    # Sort by updated date, newest first
    sorted_papers = sorted(papers.values(), key=lambda p: p.updated, reverse=True)
    return sorted_papers


@app.post("/api/fetch")
async def fetch_papers_now(background_tasks: BackgroundTasks):
    """Manually trigger paper fetching"""
    try:
        all_papers = []
        config = app.state.storage.load_config()

        for cat_config in config:
            if cat_config.enabled:
                papers = await ArXivClient.fetch_papers(
                    cat_config.category, cat_config.max_results
                )
                all_papers.extend(papers)

        # Update storage
        seen_ids = app.state.storage.load_seen_ids()
        existing_papers = app.state.storage.load_papers()

        new_count = 0
        for paper in all_papers:
            if paper.id not in seen_ids:
                paper.is_new = True
                new_count += 1
                seen_ids.add(paper.id)
            else:
                paper.is_new = False
            existing_papers[paper.id] = paper

        app.state.storage.save_papers(existing_papers)
        app.state.storage.save_seen_ids(seen_ids)

        # Update status
        status = FetchStatus(
            last_fetch=datetime.utcnow(),
            papers_found=len(all_papers),
            new_papers=new_count,
            status="success",
            message=f"Fetched {len(all_papers)} papers, {new_count} new",
        )
        app.state.storage.save_status(status)

        return {
            "status": "success",
            "papers_fetched": len(all_papers),
            "new_papers": new_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status", response_model=FetchStatus)
async def get_status():
    """Get current fetch status"""
    status = app.state.storage.load_status()
    if not status:
        return FetchStatus(
            last_fetch=None,
            papers_found=0,
            new_papers=0,
            status="no_data",
            message="No fetches performed yet",
        )
    return status


@app.post("/api/mark-all-seen")
async def mark_all_seen():
    """Mark all papers as seen"""
    papers = app.state.storage.load_papers()
    seen_ids = app.state.storage.load_seen_ids()

    for paper_id, paper in papers.items():
        paper.is_new = False
        seen_ids.add(paper_id)

    app.state.storage.save_papers(papers)
    app.state.storage.save_seen_ids(seen_ids)

    return {"status": "success", "message": "All papers marked as seen"}


@app.post("/api/toggle-auto-fetch")
async def toggle_auto_fetch():
    """Toggle automatic fetching on/off"""
    app.state.auto_fetch_enabled = not app.state.auto_fetch_enabled

    if app.state.auto_fetch_enabled and not app.state.fetch_task:
        # Restart the fetch task
        app.state.fetch_task = asyncio.create_task(periodic_fetch(app.state.__dict__))

    return {"enabled": app.state.auto_fetch_enabled}


@app.get("/api/config", response_model=List[CategoryConfig])
async def get_config():
    """Get current category configuration"""
    return app.state.storage.load_config()


@app.post("/api/config")
async def update_config(config: List[CategoryConfig]):
    """Update category configuration"""
    app.state.storage.save_config(config)
    return {"status": "success", "message": "Configuration updated"}


@app.post("/api/clear")
async def clear_all_data():
    """Clear all stored data"""
    app.state.storage.save_papers({})
    app.state.storage.save_seen_ids(set())

    # Update status
    status = FetchStatus(
        last_fetch=None,
        papers_found=0,
        new_papers=0,
        status="cleared",
        message="All data cleared",
    )
    app.state.storage.save_status(status)

    return {"status": "success", "message": "All data cleared"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
