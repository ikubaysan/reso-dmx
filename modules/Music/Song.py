from typing import List, Tuple
from modules.Music.Chart import Chart


class Song:
    def __init__(self, name: str, audio_file: str, sm_file: str, directory: str):
        """
        :param name: The name of the song
        :param audio_file: The audio file filename
        :param sm_file: The sm file filename
        :param directory: The directory of the song, containing the audio and sm files
        """
        self.name = name
        self.audio_file = audio_file
        self.sm_file = sm_file
        self.directory = directory
        self.title = ""
        self.artist = ""
        self.bpms: List[Tuple[float, float]] = []
        self.charts: List[Chart] = []
        self.duration: float = 0.0  # Song duration in seconds
