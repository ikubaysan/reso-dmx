import pytest
from modules.Music.Beat import precalculate_beats, get_beats_as_resonite_string
import os




def test_get_beats_as_resonite_string():
    from modules.Music.Song import Song
    selected_song = Song(name="Sharkmode",
                         audio_file="Sharkmode.ogg",
                         sm_file="Sharkmode.ssc",
                         directory=os.path.abspath("../../songs/15gays1pack/Sharkmode [Ky_Dash]"),
                         song_id="0"
                         )
    selected_song.load_charts_from_sm_file()
    beats = precalculate_beats(song=selected_song, chart=selected_song.charts[2], exclude_inactive_beats=True)
    resonite_string = get_beats_as_resonite_string(beats)


    # TODO: songs with stops and BPM changes

    pass