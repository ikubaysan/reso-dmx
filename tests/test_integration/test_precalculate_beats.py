import pytest
from modules.Music.Beat import precalculate_beats, get_beats_as_resonite_string
import os




def test_get_beats_as_resonite_string():
    from modules.Music.Song import Song
    selected_song = Song(name="Scars of Yesterday",
                         audio_file="Scars of Yesterday.ogg",
                         sm_file="Scars of Yesterday.sm",
                         directory=os.path.abspath("../../songs/Dragonforce 2024/Scars of Yesterday"),
                         song_id="0"
                         )
    selected_song.load_charts_from_sm_file()
    beats = precalculate_beats(song=selected_song, chart=selected_song.charts[1], exclude_inactive_beats=True)
    resonite_string = get_beats_as_resonite_string(beats[0])


    # TODO: songs with stops and BPM changes

    pass