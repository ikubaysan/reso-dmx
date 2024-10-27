from typing import List, Tuple
from modules.Music.Chart import Chart
from uuid import uuid4
import os
from typing import Tuple, List, Dict, Any
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3
from modules.Music.Chart import Chart
from pydub import AudioSegment
import logging
import uuid

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
        self.folder_name = os.path.basename(directory)
        self.title = ""
        self.artist = ""
        self.bpms: List[Tuple[float, float]] = [] # eg [(0.0, 137.7), (4.0, 138.0)]
        self.min_bpm = 0.0
        self.max_bpm = 0.0
        self.charts: List[Chart] = []
        self.duration: float = 0.0  # Song duration in seconds
        self.sample_start = 0.0
        self.sample_length = 0.0
        self.id = id
        self.detect_jacket()
        self.detect_background()
        self.uuid = str(uuid4())
        return

    def create_sample_ogg(self):
        # Check if the sample.ogg already exists
        sample_path = os.path.join(self.directory, 'reso-dmx-sample.ogg')
        if os.path.exists(sample_path):
            logger.info(f"A sample file already exists for the song {self.name} in {self.directory}")
            return

        try:
            # Load the original audio file
            audio_file_path = os.path.join(self.directory, self.audio_file)
            if self.audio_file.endswith('.mp3'):
                original_audio = AudioSegment.from_mp3(audio_file_path)
            elif self.audio_file.endswith('.ogg'):
                original_audio = AudioSegment.from_ogg(audio_file_path)
            elif self.audio_file.endswith('.wav'):
                original_audio = AudioSegment.from_wav(audio_file_path)
            else:
                logger.info(f"Unsupported audio format for the song {self.name}")
                return

            # Define the start and end time in milliseconds for the sample
            start_ms = self.sample_start * 1000
            end_ms = start_ms + (self.sample_length * 1000)

            # Cut the sample from the original audio
            sample = original_audio[start_ms:end_ms]

            # Apply fade out to the last 10% of the sample_length
            fade_duration = self.sample_length * 0.1 * 1000  # Last 10% of the sample_length
            sample_with_fadeout = sample.fade_out(int(fade_duration))

            # Export the sample as an ogg file
            sample_with_fadeout.export(sample_path, format='ogg')
            logger.info(f"Created a sample file for the song {self.name} in {self.directory}")

        except Exception as e:
            logger.error(f"Failed to create sample for {self.name} due to error: {e}")

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

        # For some reason, I noticed that in old mixes like DDR 1-8th mix,
        # some charts have 2 bpms and they're less than 1 bpm apart.
        # In this case, we'll just use the 2nd bpm, but set its start time to 0.
        if len(bpms) == 2 and bpms[-1][1] - bpms[0][1] < 1:
            bpms = [(0.0, bpms[-1][1])]

        self.min_bpm = min(item[1] for item in bpms)
        self.max_bpm = max(item[1] for item in bpms)
        self.bpms = bpms
        # Remove charts that are not mode "dance-single" (eg. "dance-double")
        self.charts = [chart for chart in charts if chart.mode == "dance-single"]
        # Sort the charts by difficulty level ascending
        self.charts.sort(key=lambda x: x.difficulty_level)

        self.duration = self.get_audio_duration(os.path.join(self.directory, self.audio_file))
        self.create_sample_ogg()
        return

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

                line = line.strip().lstrip('\ufeff')  # Remove BOM if present

                if line.startswith("#TITLE:"):
                    title = line.split(":")[1].strip()
                    title = title.rstrip(';')
                elif line.startswith("#ARTIST:"):
                    artist = line.split(":")[1].strip()
                    artist = artist.rstrip(';')
                elif line.startswith("#BPMS:"):
                    bpms_data = line.split(":")[1].strip()
                    bpms_data = bpms_data.rstrip(';')
                    # First value is the beat (integer), second value is the bpm (float, but almost always an integer)
                    # but I made both values floats here.
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
                        # Remove the : from the end of the line
                        current_mode = current_mode.rstrip(':')
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
                audio = MP3(audio_file_path)
                return float(audio.info.length)
            elif audio_file_path.endswith('.ogg'):
                audio = OggVorbis(audio_file_path)
                return float(audio.info.length)
        except Exception as e:
            logger.info(f"Error reading audio duration: {str(e)}")
        return 0.0