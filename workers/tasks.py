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
    Extracts Artist and Title from filenames like 'Artist - Title.mp3'.
    Also handles stripping the old UUID prefix if it exists.
    """
    file_stem = Path(file_path).stem

    # 1. Strip UUID prefix (if the first part is a long hex string)
    if "_" in file_stem and len(file_stem.split("_")[0]) > 30:
        file_stem = file_stem.split("_", 1)[1]

    # 2. Try to split by common separators for Artist and Title
    for sep in [" - ", " – ", "_"]:
        if sep in file_stem:
            parts = file_stem.split(sep, 1)
            return parts[0].strip(), parts[1].strip()

    # Fallback: Treat the whole thing as the title
    return None, file_stem


@celery_app.task(name="process_audio_task")
def process_audio_task(file_path: str):
    try:
        # 1. Parse metadata for Genius search
        artist, title = parse_filename(file_path)
        logger.info(f"Metadata detected - Artist: {artist}, Title: {title}")

        # 2. Run Pipeline with metadata
        # Now orchestrator can use these to find official lyrics
        sheet_text = generator.process_song(file_path, artist=artist,
                                            title=title)

        # 3. Define Output Path
        # Use the cleaned title for the final filename
        output_filename = f"{title}_final_sheet.txt"
        output_path = os.path.join(settings.PROCESSED_DATA_PATH,
                                   output_filename)

        # 4. Save the result
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sheet_text)

        return {
            "status": "COMPLETED",
            "saved_file": output_path,
            "metadata": {"artist": artist, "title": title}
        }

    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}