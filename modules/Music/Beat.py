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
    Pre-calculate the spawn times for measures and beats.
    """
    beats = []

    total_song_duration = song.duration  # Assuming the song object has a duration attribute in seconds

    if len(song.bpms) > 1:
        raise NotImplementedError("BPM changes are not supported yet.")

    current_bpm = song.bpms[0][1]

    time = 0.0
    measure_index = 0
    while measure_index < len(chart.measures):
        measure = chart.measures[measure_index]
        n_beats_in_measure = len(measure)
        time_per_beat = (4 * 60 / current_bpm) / n_beats_in_measure  # eg 4 beats per measure
        for beat in measure:
            arrows = []
            for i, note in enumerate(beat):
                if note == "1":
                    arrows.append(i)
            normalized_time = time / total_song_duration

            if exclude_inactive_beats and not arrows:
                time += time_per_beat
                continue
            else:
                beats.append(Beat(time, normalized_time, n_beats_in_measure=n_beats_in_measure, arrows_binary_string=beat, arrows=arrows))
                time += time_per_beat
        measure_index += 1
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