import subprocess
import os
from pathlib import Path


class AudioEngine:
    def __init__(self, output_dir: str = "data/processed"):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def split_stems(self, input_file: str):
        file_name = Path(input_file).name

        # Extract song name (handling your Artist - Title format)
        if "_" in file_name:
            clean_name = file_name.split("_", 1)[1]
        else:
            clean_name = file_name

        song_stem = Path(clean_name).stem
        stems = self._find_stems(song_stem)

        # Check if stems already exist
        if os.path.exists(stems["vocals"]) and os.path.exists(stems["other"]):
            print(f"Existing stems found for '{song_stem}'. Skipping Demucs.")
            return stems

        input_path = str(Path(input_file).resolve())
        output_path = str(self.output_dir)

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
        # Demucs creates: data/processed/htdemucs/[song_name]/vocals.wav
        base_path = self.output_dir / "htdemucs" / song_name
        return {
            "vocals": str(base_path / "vocals.wav"),
            "other": str(base_path / "no_vocals.wav")
        }