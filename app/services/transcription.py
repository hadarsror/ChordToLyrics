# app/services/transcription.py
import os
from typing import List, Dict
from faster_whisper import WhisperModel


class TranscriptionService:
    def __init__(self, model_size: str = "medium", device: str = "cpu"):
        # load_model can be slow, so we do it once
        self.model = WhisperModel(model_size, device=device,
                                  compute_type="int8")

    def transcribe(self, audio_path: str, initial_prompt: str = None) -> List[
        Dict]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # TUNED PARAMETERS FOR LYRICS:
        # vad_filter=True: Crucial. Skips silence so the model doesn't hallucinate or get stuck.
        # beam_size=5: Standard for accuracy without being too slow (7 was okay, but 5 is safer default).
        # condition_on_previous_text=True: Helps flow, but we add strict thresholds to prevent loops.
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
        # We must iterate completely to ensure we don't drop the generator
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