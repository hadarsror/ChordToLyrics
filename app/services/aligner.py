from typing import List, Dict
import difflib


class AlignerService:
    def sync_lyrics(self, whisper_words: List[Dict], genius_text: str) -> List[
        Dict]:
        """
        Merges the 'Correct Text' (Genius) with the 'Correct Timing' (Whisper).
        Uses SequenceMatcher to find the best fit.
        """
        if not genius_text:
            return whisper_words

        # Clean and tokenize Genius text
        # Simple whitespace splitting preserves basic flow.
        genius_tokens = genius_text.split()

        # Prepare lists for comparison (lowercase for matching)
        whisper_tokens_lower = [w['text'].lower() for w in whisper_words]
        genius_tokens_lower = [t.lower() for t in genius_tokens]

        matcher = difflib.SequenceMatcher(None, whisper_tokens_lower,
                                          genius_tokens_lower)

        synced_result = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Perfect match: Use Genius text (for casing/punctuation) + Whisper time
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    w = whisper_words[i]
                    synced_result.append({
                        "text": genius_tokens[j],
                        "start": w['start'],
                        "end": w['end'],
                        "probability": w.get('probability', 1.0)
                    })

            elif tag == 'replace':
                # Text mismatch (Whisper heard wrong). Use Whisper time, Genius text.
                # If counts differ, we interpolate the time.
                w_segment = whisper_words[i1:i2]
                if not w_segment: continue

                start_t = w_segment[0]['start']
                end_t = w_segment[-1]['end']
                duration = end_t - start_t

                g_segment = genius_tokens[j1:j2]
                count = len(g_segment)

                if count > 0:
                    step = duration / count
                    for k, word in enumerate(g_segment):
                        synced_result.append({
                            "text": word,
                            "start": round(start_t + (k * step), 3),
                            "end": round(start_t + ((k + 1) * step), 3),
                            "probability": 0.5
                            # Lower confidence since interpolated
                        })

            elif tag == 'insert':
                # Genius has words Whisper missed entirely.
                # Interpolate them between the previous and next available timestamps.
                # This fixes the "part of them" issue where lines are dropped.
                prev_end = synced_result[-1]['end'] if synced_result else 0.0

                # Find next valid start time
                next_start = prev_end + 1.0  # Default buffer
                if i1 < len(whisper_words):
                    next_start = whisper_words[i1]['start']

                duration = max(0.1, next_start - prev_end)
                g_segment = genius_tokens[j1:j2]
                count = len(g_segment)

                step = duration / count
                for k, word in enumerate(g_segment):
                    synced_result.append({
                        "text": word,
                        "start": round(prev_end + (k * step), 3),
                        "end": round(prev_end + ((k + 1) * step), 3),
                        "probability": 0.0  # Interpolated
                    })

            # 'delete' tag (Whisper has words Genius doesn't) are ignored (likely hallucinations)

        return synced_result

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
            if (is_new and words_on_line >= 4) or words_on_line >= 8:
                lines.append(" ".join(current_line))
                current_line = []
                words_on_line = 0

            if is_new:
                current_line.append(f"[{chord}] {word}")
            else:
                current_line.append(word)

            words_on_line += 1

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines).strip()