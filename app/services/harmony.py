# app/services/harmony.py
import os
from madmom.features.chords import CNNChordFeatureProcessor, CRFChordRecognitionProcessor

class HarmonyService:
    def __init__(self):
        # 1. Feature Processor (CNN)
        self.feature_processor = CNNChordFeatureProcessor()
        # 2. Decoder (CRF - Conditional Random Field)
        # This is the standard match for the CNN processor
        self.chord_processor = CRFChordRecognitionProcessor()

    def extract_chords(self, audio_path: str):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # This produces the correct feature shape for the CRF processor
        feats = self.feature_processor(audio_path)
        decoded_chords = self.chord_processor(feats)

        chords_data = []
        for start, end, label in decoded_chords:
            if label != "N":
                chords_data.append({
                    "timestamp": round(float(start), 3),
                    "label": label
                })

        return chords_data