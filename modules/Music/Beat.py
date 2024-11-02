from typing import List, Optional
from modules.Music.Song import Song
from modules.Music.Chart import Chart
import os


class Beat:
    def __init__(self, time: float, normalized_time: float, n_beats_in_measure: int, arrows_binary_string: str, arrows: List[int] = None):
        self.time = time
        self.normalized_time = normalized_time
        # 7 decimal places with padding if necessary
        self.normalized_time_string_formatted = f"{normalized_time:.7f}"

        # # pad 4 digits for the whole number part, 7 digits for the decimal part
        whole_part, decimal_part = f"{time:.7f}".split('.')
        self.time_string_formatted = f"{int(whole_part):04d}.{decimal_part:0<7}"

        self.arrows = arrows if arrows else []
        self.arrows_binary_string = arrows_binary_string
        self.n_beats_in_measure = n_beats_in_measure


def precalculate_beats(song: Song, chart: Chart, exclude_inactive_beats: bool) -> List[Beat]:
    """
    Pre-calculate the spawn times for measures and beats, handling BPM changes.
    """
    beats = []

    total_song_duration = song.duration  # Assuming the song object has a duration attribute in seconds

    bpm_list = song.bpms  # List of (beat, bpm) tuples

    current_bpm_index = 0
    current_bpm = bpm_list[current_bpm_index][1]
    next_bpm_change_beat = bpm_list[current_bpm_index + 1][0] if current_bpm_index + 1 < len(bpm_list) else None

    time = 0.0
    for measure_index, measure in enumerate(chart.measures):
        n_note_rows_in_measure = len(measure)
        for note_row_index, beat in enumerate(measure):
            # Compute the current beat number
            beat_number = measure_index * 4 + (note_row_index / n_note_rows_in_measure) * 4

            # Check for BPM change
            while next_bpm_change_beat is not None and beat_number >= next_bpm_change_beat:
                current_bpm_index += 1
                current_bpm = bpm_list[current_bpm_index][1]
                next_bpm_change_beat = bpm_list[current_bpm_index + 1][0] if current_bpm_index + 1 < len(bpm_list) else None

            # Calculate time per note row
            time_per_note_row = (4 * 60 / current_bpm) / n_note_rows_in_measure

            # Convert hold notes to regular notes
            beat = beat.replace("2", "1")

            arrows = []
            for i, note in enumerate(beat):
                if note == "1":
                    arrows.append(i)

            beat_time = time - song.offset
            beat_normalized_time = (beat_time - song.offset) / total_song_duration

            if exclude_inactive_beats and not arrows:
                time += time_per_note_row
                continue
            else:
                beats.append(Beat(
                    time=beat_time,
                    normalized_time=beat_normalized_time,
                    n_beats_in_measure=n_note_rows_in_measure,
                    arrows_binary_string=beat,
                    arrows=arrows
                ))
                time += time_per_note_row

    return beats



def get_beats_as_resonite_string(beats: List[Beat]) -> str:
    """
    Convert a list of Beat objects into a resonite string.
    """
    resonite_string = ""
    for beat in beats:
        resonite_string += f"{beat.time_string_formatted}{beat.arrows_binary_string}"
        # resonite_string += f"{beat.normalized_time_string_formatted}{beat.time_string_formatted}{beat.arrows_binary_string}"
        # resonite_string += f"{beat.normalized_time_string_formatted}{beat.arrows_binary_string}"
    return resonite_string




if __name__ == "__main__":
    selected_song = Song(name="bass 2 bass",
                         audio_file="bass 2 bass.ogg",
                         sm_file="bass 2 bass.sm",
                         directory=os.path.abspath("../../songs/DDR A/bass 2 bass"),
                         id=0)
    selected_song.load_charts()
    beats = precalculate_beats(song=selected_song, chart=selected_song.charts[3], exclude_inactive_beats=True)
    resonite_string = get_beats_as_resonite_string(beats)
    pass