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
    file_stem = Path(file_path).stem
    for sep in [" - ", " – ", "_"]:
        if sep in file_stem:
            parts = file_stem.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return "Unknown Artist", file_stem

@celery_app.task(name="process_audio_task")
def process_audio_task(file_path: str):
    try:
        artist, title = parse_filename(file_path)
        output_filename = f"{title}_final_sheet.txt"
        output_path = os.path.join(settings.PROCESSED_DATA_PATH, output_filename)

        # --- DEDUPLICATION LOGIC ---
        # If the final sheet already exists, skip AI processing entirely
        if os.path.exists(output_path):
            logger.info(f"Existing result found for {title}. Reusing data.")
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "status": "COMPLETED",
                "sheet_text": content,
                "metadata": {"artist": artist, "title": title}
            }

        # Run full pipeline if result doesn't exist
        sheet_text = generator.process_song(file_path, artist=artist, title=title)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sheet_text)

        return {
            "status": "COMPLETED",
            "sheet_text": sheet_text,
            "metadata": {"artist": artist, "title": title}
        }

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}