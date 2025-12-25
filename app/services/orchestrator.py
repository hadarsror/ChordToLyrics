# app/services/orchestrator.py
import logging
import re
# import concurrent.futures  <-- REMOVED: Cause of deadlock on CPU
from lyricsgenius import Genius
from app.core.config import settings
from app.services.audio import AudioEngine
from app.services.transcription import TranscriptionService
from app.services.harmony import HarmonyService
from app.services.aligner import AlignerService

logger = logging.getLogger(__name__)


class ChordSheetGenerator:
    def __init__(self):
        print("DEBUG: [Orchestrator] Initializing AudioEngine...", flush=True)
        self.audio_engine = AudioEngine()

        print(
            f"DEBUG: [Orchestrator] Initializing Whisper ({settings.WHISPER_MODEL_SIZE})...",
            flush=True)
        self.transcriber = TranscriptionService(
            model_size=settings.WHISPER_MODEL_SIZE,
            device=settings.INFERENCE_DEVICE
        )

        print("DEBUG: [Orchestrator] Initializing HarmonyService...",
              flush=True)
        self.harmony = HarmonyService()
        self.aligner = AlignerService()
        self.genius = Genius(settings.GENIUS_API_TOKEN)
        print("DEBUG: [Orchestrator] All services ready!", flush=True)

    def _clean_lyrics(self, text: str) -> str:
        if not text: return ""
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\d*Embed', '', text)
        text = re.sub(r'.*?Contributors', '', text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return " ".join(lines)

    def process_song(self, input_file: str, artist: str = None,
                     title: str = None):
        print(f"DEBUG: [Orchestrator] processing {input_file}...", flush=True)
        logger.info(f"Starting pipeline for: {input_file}")

        # 1. Split Stems
        print("DEBUG: [1/4] Splitting stems (Demucs)...", flush=True)
        stems = self.audio_engine.split_stems(input_file)
        print("DEBUG: [1/4] Splitting complete.", flush=True)

        prompt_guide = None
        full_lyrics_text = None

        if artist and title:
            try:
                print(f"DEBUG: Searching Genius for {artist} - {title}...",
                      flush=True)
                song = self.genius.search_song(title, artist)
                if song:
                    full_lyrics_text = self._clean_lyrics(song.lyrics)
                    prompt_guide = full_lyrics_text[:200]
                    logger.info(f"Genius lyrics found.")
                    print("DEBUG: Genius lyrics found.", flush=True)
            except Exception as e:
                logger.error(f"Genius API error: {e}")
                print(f"DEBUG: Genius API failed: {e}", flush=True)

        # 2. SEQUENTIAL EXECUTION (Fixes Deadlock)

        # Step A: Transcribe
        print("DEBUG: [2/4] Running Transcription...", flush=True)
        raw_words = self.transcriber.transcribe(stems["vocals"], prompt_guide)
        print(f"DEBUG: [2/4] Transcription done. ({len(raw_words)} segments)",
              flush=True)

        # Step B: Chords
        print("DEBUG: [3/4] Extracting Chords...", flush=True)
        chords = self.harmony.extract_chords(stems["other"])
        print(f"DEBUG: [3/4] Chords done. ({len(chords)} chords)", flush=True)

        # 3. Sync
        if full_lyrics_text:
            logger.info("Aligning Genius lyrics to Whisper timestamps...")
            final_words = self.aligner.sync_lyrics(raw_words, full_lyrics_text)
        else:
            final_words = raw_words

        # 4. Align Words to Chords
        print("DEBUG: [4/4] Aligning and generating sheet...", flush=True)
        aligned_data = self.aligner.align(final_words, chords)

        return self.aligner.generate_sheet_buffer(aligned_data)