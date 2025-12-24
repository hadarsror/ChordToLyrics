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
    Extracts Artist and Title safely.
    Only splits by '_' if it's the standard '_-_' separator.
    """
    file_stem = Path(file_path).stem

    # 1. Prioritize standard 'Artist - Title' format
    for sep in [" - ", " – ", "_-_"]:
        if sep in file_stem:
            parts = file_stem.split(sep, 1)
            return parts[0].strip(), parts[1].strip()

    # 2. Fallback: Search Genius for the full filename if no clear separator
    return None, file_stem


@celery_app.task(name="process_audio_task")
def process_audio_task(file_path: str):
    try:
        # Metadata for Genius search
        artist, title = parse_filename(file_path)

        # Use the ACTUAL file stem for output paths to ensure consistency
        file_stem = Path(file_path).stem
        output_filename = f"{file_stem}_final_sheet.txt"
        output_path = os.path.join(settings.PROCESSED_DATA_PATH,
                                   output_filename)

        # 3. Deduplication: Check if result exists
        if os.path.exists(output_path):
            logger.info(f"Existing result found for {file_stem}. Skipping AI.")
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"status": "SUCCESS", "sheet_text": content}

        # 4. Run Pipeline
        logger.info(f"Running pipeline for: {file_stem}")
        sheet_text = generator.process_song(file_path, artist=artist,
                                            title=title)

        # 5. Save the result
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sheet_text)

        return {
            "status": "SUCCESS",
            "sheet_text": sheet_text,
            "metadata": {"artist": artist, "title": title}
        }

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}