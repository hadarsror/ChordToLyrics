# app/services/orchestrator.py
import logging
import re
import concurrent.futures
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
        # Pass the model name from settings so it's easier to switch to faster models later
        self.transcriber = TranscriptionService(
            model_size=settings.WHISPER_MODEL_SIZE,
            device=settings.INFERENCE_DEVICE
        )
        self.harmony = HarmonyService()
        self.aligner = AlignerService()
        self.genius = Genius(settings.GENIUS_API_TOKEN)

    def _clean_lyrics(self, text: str) -> str:
        """Removes Genius metadata like [Verse], [Chorus], and 'Embed' junk."""
        if not text: return ""
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\d*Embed', '', text)
        text = re.sub(r'.*?Contributors', '', text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return " ".join(lines)

    def process_song(self, input_file: str, artist: str = None,
                     title: str = None):
        logger.info(f"Starting pipeline for: {input_file}")

        # 1. Split Stems (This is heavy and must happen first)
        stems = self.audio_engine.split_stems(input_file)

        prompt_guide = None
        full_lyrics_text = None

        if artist and title:
            try:
                song = self.genius.search_song(title, artist)
                if song:
                    full_lyrics_text = self._clean_lyrics(song.lyrics)
                    prompt_guide = full_lyrics_text[:200]
                    logger.info(f"Genius lyrics found.")
            except Exception as e:
                logger.error(f"Genius API error: {e}")

        # 2. Run Transcription and Chord Extraction in PARALLEL
        # This effectively cuts the processing time by doing two things at once.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start transcription
            future_transcription = executor.submit(
                self.transcriber.transcribe,
                stems["vocals"],
                prompt_guide
            )

            # Start chord extraction
            future_chords = executor.submit(
                self.harmony.extract_chords,
                stems["other"]
            )

            # Wait for both to finish
            raw_words = future_transcription.result()
            chords = future_chords.result()

        # 3. Sync (Force-Align Genius Text to Audio Timestamps)
        if full_lyrics_text:
            logger.info("Aligning Genius lyrics to Whisper timestamps...")
            final_words = self.aligner.sync_lyrics(raw_words, full_lyrics_text)
        else:
            final_words = raw_words

        # 4. Align Words to Chords
        aligned_data = self.aligner.align(final_words, chords)

        return self.aligner.generate_sheet_buffer(aligned_data)