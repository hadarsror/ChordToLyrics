import logging
from pathlib import Path
from app.services.audio import AudioEngine
from app.services.transcription import TranscriptionService
from app.services.harmony import HarmonyService
from app.services.aligner import AlignerService
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router

app = FastAPI(title="Chord Aligner AI")

# MUST HAVE FOR UI: allows your frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your UI URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "API is running"}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChordSheetGenerator:
    def __init__(self):
        self.audio_engine = AudioEngine()
        self.transcriber = TranscriptionService(model_size="base")
        self.harmony = HarmonyService()
        self.aligner = AlignerService()

    def process_song(self, input_file: str):
        logger.info(f"Starting pipeline for: {input_file}")

        # 1. Source Separation
        logger.info("Splitting stems (Vocals/Instrumental)...")
        stems = self.audio_engine.split_stems(input_file)

        # 2. Transcription (Parallelizable)
        logger.info("Transcribing lyrics...")
        words = self.transcriber.transcribe(stems["vocals"])

        # 3. Chord Detection (Parallelizable)
        logger.info("Extracting chord progression...")
        chords = self.harmony.extract_chords(stems["other"])

        # 4. Alignment
        logger.info("Synchronizing timelines...")
        aligned_data = self.aligner.align(words, chords)

        # 5. Output
        output_sheet = self.aligner.generate_sheet_buffer(aligned_data)
        return output_sheet


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_audio_file>")
        sys.exit(1)

    input_path = sys.argv[1]
    generator = ChordSheetGenerator()

    try:
        final_sheet = generator.process_song(input_path)
        print("\n--- GENERATED CHORD SHEET ---\n")
        print(final_sheet)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")