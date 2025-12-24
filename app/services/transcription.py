# app/services/transcription.py
import os
from typing import List, Dict
from faster_whisper import WhisperModel


class TranscriptionService:
    """
    Service layer for ASR (Automatic Speech Recognition) with word-level precision.
    Uses CTranslate2 backend for optimized inference.
    """

    def __init__(self, model_size: str = "medium", device: str = "cpu"):
        # Upgraded default to 'medium' for your 16GB RAM
        # compute_type="int8" allows running on consumer CPUs with low RAM
        self.model = WhisperModel(model_size, device=device,
                                  compute_type="int8")

    def transcribe(self, audio_path: str, initial_prompt: str = None) -> List[
        Dict]:
        """
        Extracts word-level timestamps from an audio file.
        Passes initial_prompt (e.g. from Genius) to guide accuracy.

        Returns:
            List of {'text': str, 'start': float, 'end': float}
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # beam_size=5 is the standard trade-off between accuracy and speed
        # initial_prompt is used here to bias the model toward the official lyrics
        segments, info = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            beam_size=5,
            initial_prompt=initial_prompt
        )

        word_data = []
        for segment in segments:
            # Check if segment has words (some segments might be music/silence)
            if segment.words:
                for word in segment.words:
                    word_data.append({
                        "text": word.word.strip(),
                        "start": round(word.start, 3),
                        "end": round(word.end, 3),
                        "probability": word.probability
                    })

        return word_data
