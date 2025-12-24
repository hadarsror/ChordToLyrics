import sys
import os
from pathlib import Path

# Add the root directory to sys.path so we can import 'app'
sys.path.append(str(Path(__file__).parent.parent))

from app.services.aligner import AlignerService
from app.services.transcription import TranscriptionService
from app.services.harmony import HarmonyService


def test_alignment_logic():
    """
    Verifies the two-pointer alignment without needing a real audio file.
    """
    print("Testing AlignerService logic...")
    aligner = AlignerService()

    # Dummy data
    mock_words = [
        {"text": "Hello", "start": 1.0, "end": 1.5},
        {"text": "world", "start": 2.0, "end": 2.5},
        {"text": "this", "start": 3.0, "end": 3.5},
        {"text": "is", "start": 4.0, "end": 4.5},
    ]

    mock_chords = [
        {"label": "C", "timestamp": 0.0},
        {"label": "G", "timestamp": 2.8},
    ]

    result = aligner.align(mock_words, mock_chords)

    # Assertions
    assert result[0]['chord'] == "C"  # 'Hello' at 1.0s should be C
    assert result[2]['chord'] == "G"  # 'this' at 3.0s should be G
    assert result[2]['is_new_chord'] == True  # Transition happened here

    print("✅ Aligner logic passed!")


def test_model_initialization():
    """
    Smoke test to check if AI models load on your hardware.
    """
    print("\nTesting AI Model loading (this may take a moment)...")
    try:
        t_service = TranscriptionService(
            model_size="tiny")  # Tiny for fast testing
        h_service = HarmonyService()
        print("✅ Models initialized successfully on your CPU!")
    except Exception as e:
        print(f"❌ Model initialization failed: {e}")


if __name__ == "__main__":
    test_alignment_logic()

    # Only run the heavy model check if specified
    if "--models" in sys.argv:
        test_model_initialization()
    else:
        print("\nNote: Run with '--models' to verify Whisper/Madmom loading.")