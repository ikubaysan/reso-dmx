from typing import List, Tuple
from modules.Music.Chart import Chart
import os
from typing import Tuple, List, Dict, Any
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from modules.Music.Chart import Chart
import logging

logger = logging.getLogger(__name__)

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
        self.bpms: List[Tuple[float, float]] = [] # eg [(0.0, 137.7), (4.0, 138.0)]
        self.charts: List[Chart] = []
        self.duration: float = 0.0  # Song duration in seconds


    def load_charts(self):
        """
        This needs to be called explicitly after the Song object is created, in order to populate the charts list.
        :param sm_file_path:
        :return:
        """
        title, artist, bpms, charts = self.parse_sm_file(os.path.join(self.directory, self.sm_file))
        self.title = title
        self.artist = artist
        self.bpms = bpms
        self.charts = charts
        self.duration = self.get_audio_duration(os.path.join(self.directory, self.audio_file))

    @staticmethod
    def parse_sm_file(sm_file_path: str) -> Tuple[str, str, List[Tuple[float, float]], List[Dict[str, Any]]]:
        title = ""
        artist = ""
        bpms = []
        charts = []

        with open(sm_file_path, 'r', encoding='utf-8') as sm_file:
            in_notes_section = False
            current_mode = ""
            current_difficulty_name = ""
            current_difficulty_level = 0
            notes_data = []

            for line in sm_file:
                line = line.strip()
                if line.startswith("#TITLE:"):
                    title = line.split(":")[1].strip()
                elif line.startswith("#ARTIST:"):
                    artist = line.split(":")[1].strip()
                elif line.startswith("#BPMS:"):
                    bpms_data = line.split(":")[1].strip()
                    bpms_data = bpms_data.rstrip(';')
                    bpms = [tuple(map(float, bpm.split("="))) for bpm in bpms_data.split(",")]
                elif line.startswith("#NOTES:"):
                    in_notes_section = True
                elif in_notes_section:
                    if line.startswith("dance-single:"):
                        current_mode = "dance-single"
                    elif line.startswith("dance-double:"):
                        current_mode = "dance-double"
                    elif line.endswith(":") and len(line) > 0 and current_difficulty_name == "":
                        current_difficulty_name = line.rstrip(':').strip()
                    elif line[:-1].isdigit() and current_difficulty_level == 0:
                        # Check if the line (excluding the last character) is a digit. Only set if it has not been set yet.
                        current_difficulty_level = int(line[:-1])
                    elif line == ",":  # Skip the comma separator
                        continue
                    elif line == ";":
                        in_notes_section = False
                        if current_mode and current_difficulty_name and current_difficulty_level:
                            chart = Chart(
                                mode=current_mode,
                                difficulty_name=current_difficulty_name,
                                difficulty_level=current_difficulty_level,
                                notes=notes_data
                            )
                            charts.append(chart)
                            current_difficulty_name = ""  # Reset difficulty name
                            current_difficulty_level = 0  # Reset difficulty level
                            notes_data = []  # Reset notes data
                    elif line.isnumeric():
                        # Capture the notes data, which looks like 0000
                        notes_data.append(line)

        return title, artist, bpms, charts

    @staticmethod
    def get_audio_duration(audio_file_path: str) -> float:
        try:
            if audio_file_path.endswith('.mp3'):
                audio = ID3(audio_file_path)
                return float(audio.info.length)
            elif audio_file_path.endswith('.ogg'):
                audio = OggVorbis(audio_file_path)
                return float(audio.info.length)
        except Exception as e:
            logger.info(f"Error reading audio duration: {str(e)}")
        return 0.0