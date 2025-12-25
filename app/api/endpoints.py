import uuid
import shutil
import os
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.core.config import settings
from app.services.orchestrator import ChordSheetGenerator

router = APIRouter()

# 1. Global In-Memory Job Store (Replaces Redis)
# Since you are the only user, a simple dictionary is perfect.
# If you restart the server, this clears, which is fine for dev/portfolio.
JOBS = {}

# Initialize the AI Orchestrator once
orchestrator = ChordSheetGenerator()


def process_song_task(task_id: str, file_path: str, artist: str, title: str):
    """
    This function runs in the background.
    It does the heavy lifting (Whisper/Demucs) without freezing the API.
    """
    try:
        JOBS[task_id]["status"] = "PROCESSING"

        # Run the full AI pipeline
        result_sheet = orchestrator.process_song(file_path, artist, title)

        JOBS[task_id]["status"] = "COMPLETED"
        JOBS[task_id]["result"] = result_sheet

    except Exception as e:
        print(f"Error processing task {task_id}: {e}")
        JOBS[task_id]["status"] = "FAILED"
        JOBS[task_id]["error"] = str(e)


@router.post("/upload")
async def upload_song(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        artist: str = None,
        title: str = None
):
    # 1. Generate unique ID
    task_id = str(uuid.uuid4())

    # 2. Save file locally
    file_location = os.path.join(settings.RAW_DATA_PATH,
                                 f"{task_id}_{file.filename}")
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Register the Job
    JOBS[task_id] = {
        "status": "PENDING",
        "filename": file.filename
    }

    # 4. Start the Background Task (Magic happens here)
    background_tasks.add_task(process_song_task, task_id, file_location,
                              artist, title)

    return {"task_id": task_id}


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    job = JOBS.get(task_id)

    if not job:
        raise HTTPException(status_code=404, detail="Task not found")

    response = {
        "task_id": task_id,
        "status": job["status"]
    }

    if job["status"] == "COMPLETED":
        response["result"] = job["result"]
    elif job["status"] == "FAILED":
        response["error"] = job.get("error", "Unknown error")

    return response