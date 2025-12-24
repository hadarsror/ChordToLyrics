# app/services/orchestrator.py
import logging
import re
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

    def _clean_lyrics(self, text: str) -> str:
        """Removes Genius metadata like [Verse], [Chorus], and header info."""
        if not text:
            return ""
        # Remove anything in brackets [Verse 1, etc]
        text = re.sub(r'\[.*?\]', '', text)
        # Remove the 'Embed' and 'Contributors' junk Genius adds at the end
        text = re.sub(r'\d*Embed', '', text)
        # Remove empty lines and leading/trailing whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return " ".join(lines)

    def process_song(self, input_file: str, artist: str = None, title: str = None):
        logger.info(f"Starting pipeline for: {input_file}")

        # 1. Source Separation
        stems = self.audio_engine.split_stems(input_file)

        # 2. Hybrid Lyrics Logic
        prompt_guide = None
        if artist and title:
            try:
                logger.info(f"Searching Genius for: {title} by {artist}")
                song = self.genius.search_song(title, artist)
                if song:
                    clean_text = self._clean_lyrics(song.lyrics)
                    # Use a much shorter prompt (first 100 chars)
                    # This biases vocab without making Whisper skip audio
                    prompt_guide = clean_text[:100]
                    logger.info("Cleaned Genius lyrics applied as prompt guide.")
            except Exception as e:
                logger.error(f"Genius API error: {e}")

        # 3. Transcription (Now using a safer, cleaned prompt)
        words = self.transcriber.transcribe(
            stems["vocals"],
            initial_prompt=prompt_guide
        )

        # 4. Chord Extraction
        chords = self.harmony.extract_chords(stems["other"])

        # 5. Temporal Alignment
        aligned_data = self.aligner.align(words, chords)

        return self.aligner.generate_sheet_buffer(aligned_data)