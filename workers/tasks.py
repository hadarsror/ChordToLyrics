# workers/tasks.py
import os
import logging
from celery import Celery
from pathlib import Path
from app.core.config import settings
from app.services.orchestrator import ChordSheetGenerator

logger = logging.getLogger(__name__)

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL,
                    backend=settings.CELERY_RESULT_BACKEND)

# --- FIX: Initialize as None (Lazy Loading) ---
# We do not instantiate the generator globally. This prevents the
# "Fork Safety" deadlock where the model loads in the parent process
# and hangs when the worker process tries to use it.
generator = None


def get_generator():
    """
    Returns the global generator instance, initializing it ONLY
    if it hasn't been created yet in this specific worker process.
    """
    global generator
    if generator is None:
        logger.info("Initializing ChordSheetGenerator (Lazy Load)...")
        print("DEBUG: Loading AI Models inside worker process...", flush=True)
        generator = ChordSheetGenerator()
    return generator


def parse_filename(file_path: str):
    """
    Extracts Artist and Title safely.
    """
    file_stem = Path(file_path).stem

    if "_-_" in file_stem:
        parts = file_stem.split("_-_", 1)
        return parts[0].strip(), parts[1].strip()

    for sep in [" - ", " – "]:
        if sep in file_stem:
            parts = file_stem.split(sep, 1)
            return parts[0].strip(), parts[1].strip()

    return "Unknown Artist", file_stem


@celery_app.task(name="process_audio_task")
def process_audio_task(file_path: str):
    try:
        # --- FIX: Get the generator safely ---
        # This triggers the model load on the first run, inside the correct process.
        gen = get_generator()

        artist, title = parse_filename(file_path)
        file_stem = Path(file_path).stem

        output_filename = f"{file_stem}_final_sheet.txt"
        output_path = os.path.join(settings.PROCESSED_DATA_PATH,
                                   output_filename)

        # Deduplication check
        if os.path.exists(output_path):
            print(f"DEBUG: File already exists at {output_path}", flush=True)
            with open(output_path, "r", encoding="utf-8") as f:
                return {"status": "SUCCESS", "sheet_text": f.read()}

        logger.info(f"Processing: {artist} - {title} (Folder: {file_stem})")

        print(f"DEBUG: 1. Starting generator.process_song for {file_stem}...",
              flush=True)

        # Use 'gen' instead of the global 'generator'
        sheet_text = gen.process_song(file_path, artist=artist,
                                      title=title)

        print(
            f"DEBUG: 2. Finished generator.process_song! Length: {len(sheet_text)}",
            flush=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sheet_text)

        return {"status": "SUCCESS", "sheet_text": sheet_text}

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        print(f"DEBUG: CRITICAL FAILURE: {str(e)}",
              flush=True)
        return {"status": "ERROR", "message": str(e)}