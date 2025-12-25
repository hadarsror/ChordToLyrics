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
        """Removes Genius metadata like [Verse], [Chorus], and 'Embed' junk."""
        if not text: return ""
        # 1. Remove anything in brackets [Verse 1, etc]
        text = re.sub(r'\[.*?\]', '', text)
        # 2. Remove the 'Embed' and 'Contributors' junk Genius adds
        text = re.sub(r'\d*Embed', '', text)
        text = re.sub(r'.*?Contributors', '', text)
        # 3. Clean up lines and join with single spaces
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return " ".join(lines)

    def process_song(self, input_file: str, artist: str = None,
                     title: str = None):
        logger.info(f"Starting pipeline for: {input_file}")
        stems = self.audio_engine.split_stems(input_file)

        prompt_guide = None
        full_lyrics_text = None

        if artist and title:
            try:
                song = self.genius.search_song(title, artist)
                if song:
                    # Clean the lyrics for alignment
                    full_lyrics_text = self._clean_lyrics(song.lyrics)

                    # For Whisper Prompt: limited context
                    prompt_guide = full_lyrics_text[:200]
                    logger.info(
                        f"Genius lyrics found. Using first 200 chars for prompt.")
            except Exception as e:
                logger.error(f"Genius API error: {e}")

        # 1. Transcribe (Get Audio Timestamps + Rough Words)
        raw_words = self.transcriber.transcribe(stems["vocals"],
                                                initial_prompt=prompt_guide)

        # 2. Sync (Force-Align Genius Text to Audio Timestamps)
        # If we have official lyrics, this fixes "Wrong Words" and "Missing Words"
        if full_lyrics_text:
            logger.info("Aligning Genius lyrics to Whisper timestamps...")
            final_words = self.aligner.sync_lyrics(raw_words, full_lyrics_text)
        else:
            final_words = raw_words

        # 3. Extract Chords
        chords = self.harmony.extract_chords(stems["other"])

        # 4. Align Words to Chords
        aligned_data = self.aligner.align(final_words, chords)

        return self.aligner.generate_sheet_buffer(aligned_data)