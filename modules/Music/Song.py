from typing import List, Tuple
from modules.Music.Chart import Chart
from uuid import uuid4
import os
from typing import Tuple, List, Dict, Any
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from modules.Music.Chart import Chart
import logging

logger = logging.getLogger(__name__)
current_id = 0

class Song:
    def __init__(self, name: str, audio_file: str, sm_file: str, directory: str, id: int):
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
        self.min_bpm = 0.0
        self.max_bpm = 0.0
        self.charts: List[Chart] = []
        self.duration: float = 0.0  # Song duration in seconds
        self.id = id
        self.detect_jacket()
        self.detect_background()

    def detect_jacket(self):
        # Look for a file whose extension is jpg or png, and filename ends with jacket (not case sensitive)
        jacket_files = [f for f in os.listdir(self.directory) if f.lower().endswith(('jacket.jpg', 'jacket.png'))]
        if jacket_files:
            self.jacket = jacket_files[0]
            return

        # Filter out files ending with "bg" or "background" before looking for any jpg or png
        other_files = [f for f in os.listdir(self.directory)
                       if (f.lower().endswith(('.jpg', '.png'))
                           and not any(
                        f.lower().endswith(bg) for bg in ('bg.jpg',
                                                          'bg.png',
                                                          'background.jpg',
                                                          'background.png')))]

        self.jacket = other_files[0] if other_files else None

    def detect_background(self):
        # Look for a file whose extension is jpg or png, and filename ends with background (not case sensitive)
        background_files = [f for f in os.listdir(self.directory) if f.lower().endswith(('bg.jpg',
                                                                                         'bg.png',
                                                                                         'background.jpg',
                                                                                         'background.png'))]
        self.background = background_files[0] if background_files else None

    def load_charts(self):
        """
        This needs to be called explicitly after the Song object is created, in order to populate the charts list.
        :param sm_file_path:
        :return:
        """
        title, artist, sample_start, sample_length, bpms, charts = self.parse_sm_file(os.path.join(self.directory, self.sm_file))
        self.title = title
        self.artist = artist
        self.sample_start = sample_start
        self.sample_length = sample_length
        self.min_bpm = min(item[1] for item in bpms)
        self.max_bpm = max(item[1] for item in bpms)
        self.bpms = bpms
        self.charts = charts
        self.duration = self.get_audio_duration(os.path.join(self.directory, self.audio_file))

    @staticmethod
    def parse_sm_file(sm_file_path: str) -> Tuple[str, str, float, float, List[Tuple[float, float]], List[Dict[str, Any]]]:
        title = ""
        artist = ""
        bpms = []
        charts = []
        sample_start = 0.0
        sample_length = 0.0

        with open(sm_file_path, 'r', encoding='utf-8') as sm_file:
            in_notes_section = False
            current_mode = ""
            current_difficulty_name = ""
            current_difficulty_level = 0
            notes_data = []
            measures = []  # List to store notes for the current measure

            for line in sm_file:
                line = line.strip()
                if line.startswith("#TITLE:"):
                    title = line.split(":")[1].strip()
                    title = title.rstrip(';')
                elif line.startswith("#ARTIST:"):
                    artist = line.split(":")[1].strip()
                    artist = artist.rstrip(';')
                elif line.startswith("#BPMS:"):
                    bpms_data = line.split(":")[1].strip()
                    bpms_data = bpms_data.rstrip(';')
                    bpms = [tuple(map(float, bpm.split("="))) for bpm in bpms_data.split(",")]
                elif line.startswith("#NOTES:"):
                    in_notes_section = True
                elif line.startswith("#SAMPLESTART:"):
                    # Eg. line = "#SAMPLESTART:61.34;"
                    # Split by ':', take the second part, split by ';', and cast to float.
                    sample_start = float(line.split(':')[1].split(';')[0])
                elif line.startswith("#SAMPLELENGTH:"):
                    # Eg. line = "#SAMPLELENGTH:10.00;"
                    # Split by ':', take the second part, split by ';', and cast to float.
                    sample_length = float(line.split(':')[1].split(';')[0])
                elif in_notes_section:
                    if line.startswith("dance-single:") or line.startswith("dance-double:"):
                        current_mode = line.strip()  # Set the current mode
                    elif line.endswith(":") and len(line) > 0 and current_difficulty_name == "":
                        current_difficulty_name = line.rstrip(':').strip()
                    elif line[:-1].isdigit() and current_difficulty_level == 0:
                        # Check if the line (excluding the last character) is a digit. Only set if it has not been set yet.
                        current_difficulty_level = int(line[:-1])
                    elif line == ",":  # End of measure
                        measures.append(notes_data)  # Add notes data for the current measure
                        notes_data = []  # Reset notes data for the next measure
                    elif line == ";":
                        in_notes_section = False
                        if current_mode and current_difficulty_name and current_difficulty_level:
                            chart = Chart(
                                mode=current_mode,
                                difficulty_name=current_difficulty_name,
                                difficulty_level=current_difficulty_level,
                                measures=measures  # Store measures as a list
                            )
                            charts.append(chart)
                            current_difficulty_name = ""  # Reset difficulty name
                            current_difficulty_level = 0  # Reset difficulty level
                            notes_data = []  # Reset notes data
                            measures = []  # Reset measures
                    elif line.isnumeric():
                        # Capture the notes data, which looks like 0000
                        notes_data.append(line)

        return title, artist, sample_start, sample_length, bpms, charts

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