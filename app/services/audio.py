# app/services/audio.py
import subprocess
import os
from pathlib import Path

class AudioEngine:
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def split_stems(self, input_file: str):
        # FIX: Use the full filename stem (e.g., 'Hayley_Williams_-_Hard')
        # This ensures we look in the exact folder Demucs creates.
        song_stem = Path(input_file).stem
        stems = self._find_stems(song_stem)

        # Check if stems already exist (Deduplication)
        if os.path.exists(stems["vocals"]) and os.path.exists(stems["other"]):
            print(f"Existing stems found for '{song_stem}'. Reusing them.")
            return stems

        input_path = str(Path(input_file).resolve())
        output_path = str(self.output_dir)

        # Demucs creates: [output_dir]/htdemucs/[song_stem]/vocals.wav
        cmd = [
            "demucs",
            "--two-stems", "vocals",
            "-o", output_path,
            input_path
        ]

        print(f"Running Demucs: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Demucs failed: {result.stderr}")

        return stems

    def _find_stems(self, song_name: str):
        base_path = self.output_dir / "htdemucs" / song_name
        return {
            "vocals": str(base_path / "vocals.wav"),
            "other": str(base_path / "no_vocals.wav")
        }