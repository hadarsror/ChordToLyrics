import uuid
import shutil
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.core.config import settings
from app.services.orchestrator import ChordSheetGenerator

router = APIRouter()

# 1. Global In-Memory Job Store
JOBS = {}

# Initialize the AI Orchestrator once
orchestrator = ChordSheetGenerator()


def parse_filename(filename: str):
    """
    Extracts Artist and Title from the filename string.
    """
    file_stem = Path(filename).stem

    # Check for the sanitized separator '_-_'
    if "_-_" in file_stem:
        parts = file_stem.split("_-_", 1)
        return parts[0].strip(), parts[1].strip()

    # Check for standard dash separators
    for sep in [" - ", " – "]:
        if sep in file_stem:
            parts = file_stem.split(sep, 1)
            return parts[0].strip(), parts[1].strip()

    return None, None


def process_song_task(task_id: str, file_path: str, artist: str, title: str,
                      original_filename: str):
    """
    Runs the AI pipeline in the background.
    """
    try:
        JOBS[task_id]["status"] = "PROCESSING"

        # 1. Run the full AI pipeline
        # The orchestrator will now see a clean filepath (e.g., "data/raw/Song.mp3")
        # preventing Demucs from creating folders with UUIDs.
        result_sheet = orchestrator.process_song(file_path, artist, title)

        # 2. Save the result to disk
        file_stem = Path(original_filename).stem
        output_filename = f"{file_stem}_final_sheet.txt"
        output_path = os.path.join(settings.PROCESSED_DATA_PATH,
                                   output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result_sheet)

        # 3. Update Job Status
        JOBS[task_id]["status"] = "COMPLETED"
        JOBS[task_id]["result"] = result_sheet
        JOBS[task_id]["output_path"] = output_path

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
    # 1. Generate unique ID for the Job (Still needed for the frontend to track status)
    task_id = str(uuid.uuid4())

    # 2. Smart Metadata Extraction
    if not artist or not title:
        parsed_artist, parsed_title = parse_filename(file.filename)
        if parsed_artist and parsed_title:
            artist = artist or parsed_artist
            title = title or parsed_title

    # 3. Save raw file locally - WITHOUT UUID
    # We use the original filename. Be aware this overwrites files with the same name.
    file_location = os.path.join(settings.RAW_DATA_PATH, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Register the Job
    JOBS[task_id] = {
        "status": "PENDING",
        "filename": file.filename
    }

    # 5. Start the Background Task
    background_tasks.add_task(
        process_song_task,
        task_id,
        file_location,
        artist,
        title,
        file.filename
    )

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