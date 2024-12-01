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
    total_song_duration = song.duration  # Ensure this includes the duration added by stops
    bpm_list = song.bpms  # List of (beat, bpm) tuples
    stop_list = song.stops  # List of (beat, duration) tuples

    # Combine BPM changes and stops into a single sorted event list
    timing_events = [{'beat': beat, 'type': 'BPM', 'value': bpm} for beat, bpm in bpm_list]
    timing_events += [{'beat': beat, 'type': 'STOP', 'value': duration} for beat, duration in stop_list]
    timing_events.sort(key=lambda x: x['beat'])

    current_bpm = bpm_list[0][1]
    current_time = -song.offset  # Start time adjusted by song offset
    current_beat = 0.0
    event_index = 0

    note_count = 0

    for measure_index, measure in enumerate(chart.measures):
        n_note_rows_in_measure = len(measure)
        for note_row_index, beat in enumerate(measure):
            beat_fraction = note_row_index / n_note_rows_in_measure
            beat_number = measure_index * 4 + beat_fraction * 4

            # Process all timing events up to the current beat
            while event_index < len(timing_events) and timing_events[event_index]['beat'] <= beat_number:
                event = timing_events[event_index]
                delta_beats = event['beat'] - current_beat
                delta_time = (delta_beats * 60) / current_bpm
                current_time += delta_time
                current_beat = event['beat']

                if event['type'] == 'BPM':
                    current_bpm = event['value']
                elif event['type'] == 'STOP':
                    current_time += event['value']  # Adjust time for the stop

                event_index += 1

            # Compute time from current_beat to beat_number
            delta_beats = beat_number - current_beat
            delta_time = (delta_beats * 60) / current_bpm
            current_time += delta_time
            current_beat = beat_number

            # Determine arrows and update note count
            arrows_binary_string = beat.replace("2", "1").replace("4", "1")
            arrows = [i for i, note in enumerate(arrows_binary_string) if note == "1"]
            note_count += len(arrows)

            # Compute normalized time
            beat_normalized_time = current_time / total_song_duration

            if exclude_inactive_beats and not arrows:
                continue
            else:
                beats.append(Beat(
                    time=current_time,
                    normalized_time=beat_normalized_time,
                    n_beats_in_measure=n_note_rows_in_measure,
                    arrows_binary_string=arrows_binary_string,
                    arrows=arrows
                ))

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
    selected_song.load_charts_from_sm_file()
    beats = precalculate_beats(song=selected_song, chart=selected_song.charts[3], exclude_inactive_beats=True)
    resonite_string = get_beats_as_resonite_string(beats)
    pass