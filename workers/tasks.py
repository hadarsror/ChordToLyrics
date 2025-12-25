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
generator = ChordSheetGenerator()


def parse_filename(file_path: str):
    """
    Extracts Artist and Title safely by looking for the
    sanitized separator '_-_' first.
    """
    file_stem = Path(file_path).stem

    # Check for the sanitized version of " - " first
    if "_-_" in file_stem:
        parts = file_stem.split("_-_", 1)
        return parts[0].strip(), parts[1].strip()

    # Fallback to standard dash if it exists
    for sep in [" - ", " – "]:
        if sep in file_stem:
            parts = file_stem.split(sep, 1)
            return parts[0].strip(), parts[1].strip()

    # If no separator, the whole thing is the title
    return "Unknown Artist", file_stem


@celery_app.task(name="process_audio_task")
def process_audio_task(file_path: str):
    try:
        artist, title = parse_filename(file_path)
        file_stem = Path(file_path).stem

        # We always use the FULL file_stem for paths to match Demucs folder names
        output_filename = f"{file_stem}_final_sheet.txt"
        output_path = os.path.join(settings.PROCESSED_DATA_PATH,
                                   output_filename)

        # Deduplication check
        if os.path.exists(output_path):
            print(f"DEBUG: File already exists at {output_path}", flush=True)
            with open(output_path, "r", encoding="utf-8") as f:
                return {"status": "SUCCESS", "sheet_text": f.read()}

        logger.info(f"Processing: {artist} - {title} (Folder: {file_stem})")

        # --- DEBUG START ---
        print(f"DEBUG: 1. Starting generator.process_song for {file_stem}...",
              flush=True)

        sheet_text = generator.process_song(file_path, artist=artist,
                                            title=title)

        print(
            f"DEBUG: 2. Finished generator.process_song! Length: {len(sheet_text)}",
            flush=True)
        # --- DEBUG END ---

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sheet_text)

        return {"status": "SUCCESS", "sheet_text": sheet_text}

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        print(f"DEBUG: CRITICAL FAILURE: {str(e)}",
              flush=True)  # Catch silent crashes
        return {"status": "ERROR", "message": str(e)}