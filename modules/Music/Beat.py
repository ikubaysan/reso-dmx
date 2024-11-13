from typing import List, Optional
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


def precalculate_beats(song, chart, exclude_inactive_beats: bool) -> (List[Beat], int):
    """
    Pre-calculate the spawn times for measures and beats, handling BPM changes and stops.

    :param song: The song object containing BPM and stop information.
    :param chart: The chart object containing measure and beat data.
    :param exclude_inactive_beats: Whether to exclude beats with no arrows.

    :return: A tuple containing a list of Beat objects and the total note count.
    """
    beats = []
    total_song_duration = song.duration  # Assuming the song object has a duration attribute in seconds
    bpm_list = song.bpms  # List of (beat, bpm) tuples
    stop_list = song.stops  # List of (beat, duration) tuples

    current_bpm_index = 0
    current_bpm = bpm_list[current_bpm_index][1]
    next_bpm_change_beat = bpm_list[current_bpm_index + 1][0] if current_bpm_index + 1 < len(bpm_list) else None

    current_stop_index = 0
    next_stop_beat = stop_list[current_stop_index][0] if stop_list else None
    stop_time_accumulated = 0.0  # Accumulated stop time to adjust future beat times

    time = 0.0
    note_count = 0

    for measure_index, measure in enumerate(chart.measures):
        n_note_rows_in_measure = len(measure)
        for note_row_index, beat in enumerate(measure):
            beat_number = measure_index * 4 + (note_row_index / n_note_rows_in_measure) * 4

            # Check for BPM change
            while next_bpm_change_beat is not None and beat_number >= next_bpm_change_beat:
                current_bpm_index += 1
                current_bpm = bpm_list[current_bpm_index][1]
                next_bpm_change_beat = bpm_list[current_bpm_index + 1][0] if current_bpm_index + 1 < len(bpm_list) else None

            # Check for a stop at this beat and adjust time accordingly
            while next_stop_beat is not None and beat_number >= next_stop_beat:
                stop_duration = stop_list[current_stop_index][1]
                stop_time_accumulated += stop_duration
                current_stop_index += 1
                next_stop_beat = stop_list[current_stop_index][0] if current_stop_index < len(stop_list) else None

            # Calculate time per note row considering the current BPM
            time_per_note_row = (4 * 60 / current_bpm) / n_note_rows_in_measure

            # Determine arrows, replace '2' (start of holds)
            # and '4' (start of rolls) with '1's (taps) in arrows_binary_string,
            # and update note count
            arrows_binary_string = beat.replace("2", "1").replace("4", "1")
            arrows = [i for i, note in enumerate(arrows_binary_string) if note == "1"]
            note_count += len(arrows)

            # Adjust beat time for stops and compute normalized time
            beat_time = time + stop_time_accumulated - song.offset
            beat_normalized_time = beat_time / total_song_duration

            if exclude_inactive_beats and not arrows:
                time += time_per_note_row
                continue
            else:
                beats.append(Beat(
                    time=beat_time,
                    normalized_time=beat_normalized_time,
                    n_beats_in_measure=n_note_rows_in_measure,
                    arrows_binary_string=arrows_binary_string,  # Use the modified string
                    arrows=arrows
                ))

            time += time_per_note_row  # Advance the time for the next beat

    return beats, note_count







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
    from modules.Music.Song import Song
    selected_song = Song(name="bass 2 bass",
                         audio_file="bass 2 bass.ogg",
                         sm_file="bass 2 bass.sm",
                         directory=os.path.abspath("../../songs/DDR A/bass 2 bass"),
                         id=0)
    selected_song.load_charts()
    beats = precalculate_beats(song=selected_song, chart=selected_song.charts[3], exclude_inactive_beats=True)
    resonite_string = get_beats_as_resonite_string(beats)
    pass