import os
import shutil
import re
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings
from workers.tasks import process_audio_task
from app.models.schemas import TaskResponse

router = APIRouter()

def sanitize_filename(filename: str) -> str:
    """Removes special characters to avoid shell errors in Demucs."""
    name, ext = os.path.splitext(filename)
    # Replace non-alphanumeric with underscores
    clean_name = re.sub(r'[^\w\s-]', '', name).replace(' ', '_')
    return f"{clean_name}{ext}"

@router.post("/upload", response_model=TaskResponse)
async def upload_audio(file: UploadFile = File(...)):
    # Sanitize the filename (No UUID, keeps your metadata)
    filename = sanitize_filename(file.filename)
    storage_path = os.path.join(settings.RAW_DATA_PATH, filename)

    # Save file to disk
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Trigger background worker
    task = process_audio_task.delay(storage_path)
    return {"task_id": task.id, "status": "PENDING"}

@router.get("/status/{task_id}")
async def get_status(task_id: str):
    from workers.tasks import celery_app
    task_result = celery_app.AsyncResult(task_id)

    if task_result.state == "PENDING":
        return {"status": "PENDING", "result": None}

    elif task_result.state == "SUCCESS":
        res = task_result.result
        # Handle result dictionary from worker
        if isinstance(res, dict) and res.get("status") == "ERROR":
            return {"status": "FAILURE", "result": res.get("message")}
        return {"status": "SUCCESS", "result": res.get("sheet_text")}

    elif task_result.state == "FAILURE":
        return {"status": "FAILURE", "result": str(task_result.info)}

    return {"status": task_result.state, "result": None}