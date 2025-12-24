# app/services/orchestrator.py
import logging
from lyricsgenius import Genius
from app.core.config import settings
from app.services.audio import AudioEngine
from app.services.transcription import TranscriptionService
from app.services.harmony import HarmonyService
from app.services.aligner import AlignerService

logger = logging.getLogger(__name__)


class ChordSheetGenerator:
    def __init__(self):
        self.audio_engine = AudioEngine()
        self.transcriber = TranscriptionService(model_size="medium")
        self.harmony = HarmonyService()
        self.aligner = AlignerService()
        self.genius = Genius(settings.GENIUS_API_TOKEN)

    def process_song(self, input_file: str, artist: str = None,
                     title: str = None):
        logger.info(f"Starting pipeline for: {input_file}")

        # 1. Source Separation (Returns paths to the .wav files you want)
        stems = self.audio_engine.split_stems(input_file)

        # 2. Hybrid Lyrics Logic
        official_lyrics = None
        prompt_guide = None

        if artist and title:
            try:
                logger.info(f"Searching Genius for: {title} by {artist}")
                song = self.genius.search_song(title, artist)
                if song:
                    official_lyrics = song.lyrics
                    # Smart Truncation fix: prevents Whisper from skipping the start
                    prompt_guide = official_lyrics[:300].rsplit(' ', 1)[0]
                    logger.info(
                        "Official lyrics found. Truncated prompt guide created.")
            except Exception as e:
                logger.error(f"Genius API error: {e}")

        # 3. Transcription (Guidance with truncated prompt)
        # It uses stems['vocals'] which you can now find in your data/processed folder
        words = self.transcriber.transcribe(
            stems["vocals"],
            initial_prompt=prompt_guide
        )

        # 4. Chord Extraction
        chords = self.harmony.extract_chords(stems["other"])

        # 5. Temporal Alignment
        aligned_data = self.aligner.align(words, chords)

        return self.aligner.generate_sheet_buffer(aligned_data)