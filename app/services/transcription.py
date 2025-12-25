# app/services/transcription.py
import os
from typing import List, Dict
from faster_whisper import WhisperModel

class TranscriptionService:
    def __init__(self, model_size: str = "medium", device: str = "cpu"):
        self.model = WhisperModel(model_size, device=device, compute_type="int8")

    def transcribe(self, audio_path: str, initial_prompt: str = None) -> List[Dict]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # beam_size=7 increases accuracy for difficult vocals
        # initial_prompt provides the vocab hint from Genius
        segments, info = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            beam_size=7,
            initial_prompt=initial_prompt,
            condition_on_previous_text=False,
            language="en"
        )

        word_data = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    word_data.append({
                        "text": word.word.strip(),
                        "start": round(word.start, 3),
                        "end": round(word.end, 3),
                        "probability": word.probability
                    })
        return word_data