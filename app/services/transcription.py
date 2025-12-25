# app/services/transcription.py
import os
from typing import List, Dict
from faster_whisper import WhisperModel
from app.core.config import settings


class TranscriptionService:
    def __init__(self, model_size: str = "medium", device: str = None):
        # Use config defaults if not provided
        device = device or settings.INFERENCE_DEVICE
        compute_type = settings.COMPUTE_TYPE

        print(
            f"Loading Whisper Model: {model_size} on {device} ({compute_type})")
        self.model = WhisperModel(model_size, device=device,
                                  compute_type=compute_type)

    def transcribe(self, audio_path: str, initial_prompt: str = None) -> List[
        Dict]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # We keep beam_size=5 for maximum quality.
        # The speedup comes from VAD (skipping silence) and GPU usage.
        segments, info = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            beam_size=5,
            initial_prompt=initial_prompt,
            condition_on_previous_text=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
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