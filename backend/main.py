import os
from pathlib import Path
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio
import logging

from git_ops import GitOperations
from agent import AgentManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="VV Backend API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base path from environment
WEBAPP_BASE_PATH = os.getenv("WEBAPP_BASE_PATH", "/Users/danny/src/vv")

# Initialize managers
git_ops = GitOperations(WEBAPP_BASE_PATH)
agent_manager = AgentManager(WEBAPP_BASE_PATH, git_ops=git_ops)

# Global state for merge queue
merge_queue: List[int] = []
merge_in_progress: bool = False


# Pydantic models
class AgentRequest(BaseModel):
    prompt: str


class CreatePaneResponse(BaseModel):
    pane_id: int
    branch: str
    status: str
    message: str


class PaneStatus(BaseModel):
    pane_id: int
    active: bool
    branch: str | None
    is_ahead: bool
    is_stale: bool
    agent_running: bool


class OrchestrationState(BaseModel):
    panes: List[PaneStatus]


class MergeQueueItem(BaseModel):
    pane_id: int
    status: str


# API Endpoints

@app.get("/")
async def root():
    return {"message": "VV Backend API", "version": "1.0"}


@app.post("/api/panes/{pane_id}/create", response_model=CreatePaneResponse)
async def create_pane(pane_id: int):
    """
    Initialize a pane by creating a new git branch.
    """
    if pane_id < 1 or pane_id > 6:
        raise HTTPException(status_code=400, detail="Pane ID must be between 1 and 6")
    
    result = git_ops.create_pane_branch(pane_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return CreatePaneResponse(
        pane_id=pane_id,
        branch=result["branch"],
        status=result["status"],
        message=result["message"]
    )


@app.get("/api/orchestration", response_model=OrchestrationState)
async def get_orchestration_state():
    """
    Get the current status of all 6 panes.
    Polls git status for each pane.
    """
    panes = []
    
    for pane_id in range(1, 7):
        status = git_ops.get_branch_status(pane_id)
        agent_running = agent_manager.is_agent_running(pane_id)
        
        panes.append(PaneStatus(
            pane_id=pane_id,
            active=status.get("active", False),
            branch=status.get("branch"),
            is_ahead=status.get("is_ahead", False),
            is_stale=status.get("is_stale", False),
            agent_running=agent_running
        ))
    
    return OrchestrationState(panes=panes)


@app.post("/api/panes/{pane_id}/agent")
async def start_agent(pane_id: int, request: AgentRequest):
    """
    Start a cursor-agent run for a pane.
    """
    if pane_id < 1 or pane_id > 6:
        raise HTTPException(status_code=400, detail="Pane ID must be between 1 and 6")
    
    result = await agent_manager.start_agent(pane_id, request.prompt)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@app.get("/api/panes/{pane_id}/agent/stream")
async def stream_agent_output(pane_id: int):
    """
    SSE endpoint to stream agent output in real-time.
    """
    if pane_id < 1 or pane_id > 6:
        raise HTTPException(status_code=400, detail="Pane ID must be between 1 and 6")
    
    async def event_generator():
        async for line in agent_manager.stream_agent_output(pane_id):
            yield f"data: {line}\n\n"
        
        # Send end signal
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/panes/{pane_id}/merge")
async def merge_pane(pane_id: int):
    """
    Merge a pane's branch into main.
    Adds to queue for sequential processing.
    """
    if pane_id < 1 or pane_id > 6:
        raise HTTPException(status_code=400, detail="Pane ID must be between 1 and 6")
    
    # Check if pane has an agent running
    if agent_manager.is_agent_running(pane_id):
        raise HTTPException(status_code=400, detail="Cannot merge while agent is running")
    
    # Add to merge queue
    if pane_id not in merge_queue:
        merge_queue.append(pane_id)
        
        # Start processing if not already in progress
        if not merge_in_progress:
            asyncio.create_task(process_merge_queue())
    
    return {
        "status": "queued",
        "message": f"Pane {pane_id} added to merge queue",
        "queue_position": merge_queue.index(pane_id)
    }


@app.get("/api/merge-queue")
async def get_merge_queue():
    """
    Get the current merge queue status.
    """
    return {
        "queue": [{"pane_id": pid, "status": "queued"} for pid in merge_queue],
        "in_progress": merge_in_progress
    }


async def process_merge_queue():
    """
    Process merge queue sequentially.
    """
    global merge_in_progress
    
    merge_in_progress = True
    
    try:
        while merge_queue:
            pane_id = merge_queue[0]
            
            logger.info(f"Processing merge for pane {pane_id}")
            
            try:
                result = git_ops.merge_pane(pane_id)
                
                if result["status"] == "error":
                    logger.error(f"Merge failed for pane {pane_id}: {result['message']}")
                else:
                    logger.info(f"Merge successful for pane {pane_id}")
                
            except Exception as e:
                logger.error(f"Exception during merge for pane {pane_id}: {e}")
            
            # Remove from queue
            merge_queue.pop(0)
            
            # Small delay between merges
            await asyncio.sleep(1)
    
    finally:
        merge_in_progress = False


@app.delete("/api/panes/{pane_id}")
async def delete_pane(pane_id: int):
    """
    Reset a pane by checking out main branch.
    Cannot delete if agent is running or merge is in progress.
    """
    if pane_id < 1 or pane_id > 6:
        raise HTTPException(status_code=400, detail="Pane ID must be between 1 and 6")
    
    # Check if agent is running
    if agent_manager.is_agent_running(pane_id):
        raise HTTPException(status_code=400, detail="Cannot close pane while agent is running")
    
    # Check if in merge queue
    if pane_id in merge_queue:
        raise HTTPException(status_code=400, detail="Cannot close pane while merge is pending")
    
    # Checkout main to "deactivate" the pane
    pane_path = git_ops.get_pane_path(pane_id)
    
    try:
        from git import Repo
        repo = Repo(pane_path)
        
        if repo.is_dirty():
            repo.git.reset('--hard')
            repo.git.clean('-fd')
        
        repo.git.checkout('main')
        
        return {
            "status": "success",
            "message": f"Pane {pane_id} reset to main"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

