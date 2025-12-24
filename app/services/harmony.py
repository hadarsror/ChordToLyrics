import os
import numpy as np
from madmom.features.chords import DeepChromaChordRecognitionProcessor, \
    CNNChordFeatureProcessor


class HarmonyService:
    def __init__(self):
        # This processor uses a CNN to extract robust harmonic features
        self.feature_processor = CNNChordFeatureProcessor()
        # This processor decodes those features into actual chord labels (C, G, Am, etc.)
        self.chord_processor = DeepChromaChordRecognitionProcessor()

    def extract_chords(self, audio_path: str):
        """
        Uses Deep Learning to extract chords with high temporal precision.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 1. Extract features using CNN
        feats = self.feature_processor(audio_path)

        # 2. Decode features into chords with timestamps
        # Returns an array of (start, end, label)
        decoded_chords = self.chord_processor(feats)

        chords_data = []
        for start, end, label in decoded_chords:
            # We filter out 'N' (No chord/Silence) to keep the sheet clean
            if label != "N":
                chords_data.append({
                    "timestamp": round(float(start), 3),
                    "label": label
                })

        return chords_data