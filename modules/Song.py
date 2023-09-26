from typing import List, Tuple, Dict, Any


class Song:
    def __init__(self, name: str, audio_file: str, sm_file: str, directory: str):
        self.name = name
        self.audio_file = audio_file
        self.sm_file = sm_file
        self.directory = directory
        self.title = ""
        self.artist = ""
        self.bpms: List[Tuple[float, float]] = []
        self.charts: List[Dict[str, Any]] = []  # List of dictionaries containing charts data
        self.duration: float = 0.0  # Song duration in seconds
