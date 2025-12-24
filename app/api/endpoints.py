import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings
from workers.tasks import process_audio_task
from app.models.schemas import TaskResponse

router = APIRouter()

@router.post("/upload", response_model=TaskResponse)
async def upload_audio(file: UploadFile = File(...)):
    # 1. Use the original filename instead of a UUID
    # os.path.basename prevents directory traversal attacks
    filename = os.path.basename(file.filename)
    storage_path = os.path.join(settings.RAW_DATA_PATH, filename)

    # 2. Save file to disk (Overwrites existing to keep data/raw clean)
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Trigger background worker
    # Since filename is static, AudioEngine can now hit the cache
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
        # Ensure result is serializable and handle error dicts from worker
        if isinstance(res, dict) and res.get("status") == "ERROR":
            return {"status": "FAILURE", "result": res.get("message")}
        return {"status": "SUCCESS", "result": str(res)}

    elif task_result.state == "FAILURE":
        return {"status": "FAILURE", "result": str(task_result.info)}

    return {"status": task_result.state, "result": None}