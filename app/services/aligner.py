from typing import List, Dict


class AlignerService:
    def align(self, words: List[Dict], chords: List[Dict]) -> List[Dict]:
        """
        Synchronizes lyrics and chords using a two-pointer approach.
        Assumes both inputs are pre-sorted by timestamp.
        """
        aligned_result = []
        last_seen_chord = None
        chord_idx = 0
        num_chords = len(chords)

        for word in words:
            t_start = word['start']

            # Advance chord pointer until we find the chord active at t_start
            while (chord_idx + 1 < num_chords and
                   chords[chord_idx + 1]['timestamp'] <= t_start):
                chord_idx += 1

            current_label = chords[chord_idx]['label'] if chords else "N/A"
            is_transition = (current_label != last_seen_chord)

            aligned_result.append({
                "word": word['text'],  # Storing as 'word'
                "chord": current_label,
                "is_new_chord": is_transition,
                "start": t_start,
                "end": word['end']
            })

            last_seen_chord = current_label

        return aligned_result

    def generate_sheet_buffer(self, aligned_data: List[Dict]) -> str:
        """
        Formats the lyrics into a structured song sheet with line breaks.
        """
        lines = []
        current_line = []
        words_on_line = 0

        for item in aligned_data:
            word = item['word']
            chord = item['chord']
            is_new = item['is_new_chord']

            # Logic for line breaks:
            # 1. Start new line if a new chord appears after at least 4 words
            # 2. OR start new line if the current line exceeds 8 words
            if (is_new and words_on_line >= 4) or words_on_line >= 8:
                lines.append(" ".join(current_line))
                current_line = []
                words_on_line = 0

            if is_new:
                current_line.append(f"[{chord}] {word}")
            else:
                current_line.append(word)

            words_on_line += 1

        # Append the final line if it contains data
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines).strip()