import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from celery.result import AsyncResult
from app.core.config import settings

# This imports the task name so we can send work to it
# We use send_task to avoid importing heavy libraries in the API
from workers.tasks import celery_app

router = APIRouter()


@router.post("/upload")
async def upload_song(file: UploadFile = File(...)):
    # 1. Save the file locally so the Worker can find it
    file_location = os.path.join(settings.RAW_DATA_PATH, file.filename)

    # Write the uploaded file to disk
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Send the task to the Worker (Celery)
    # "process_audio_task" matches the name in workers/tasks.py
    task = celery_app.send_task("process_audio_task", args=[file_location])

    # 3. Return the Task ID to the user immediately
    return {"task_id": task.id}


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    # 1. Ask Redis about the status of this task ID
    task_result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task_result.status,  # PENDING, STARTED, SUCCESS, FAILURE
    }

    # 2. If finished, attach the result
    if task_result.status == "SUCCESS":
        # The worker returns a dict like {"status": "SUCCESS", "sheet_text": "..."}
        # We extract the sheet_text from it
        data = task_result.result
        if isinstance(data, dict) and "sheet_text" in data:
            response["result"] = data["sheet_text"]
        else:
            response["result"] = str(data)

    elif task_result.status == "FAILURE":
        response["error"] = str(task_result.result)

    return response