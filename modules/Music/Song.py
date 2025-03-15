from typing import List, Tuple, Any, Optional
from modules.Music.Chart import Chart
from uuid import uuid4
from modules.utils.FileUtils import read_file_with_encodings
import os
from typing import Tuple, List, Dict, Any
from mutagen.id3 import ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3
from modules.Music.Chart import Chart
from pydub import AudioSegment
from modules.utils.StringUtils import format_seconds
import logging
import json
import simfile
from simfile.notes import NoteData as SimfileNoteData
from simfile.timing import Beat as SimfileBeat

logger = logging.getLogger(__name__)
current_id = 0

class Song:
    def __init__(self, song_id: Optional[str], name: str, audio_file: str, directory: str, sm_file: str, sm_file_contents: Optional[str] = None):
        """
        :param name: The name of the song
        :param audio_file: The audio file filename
        :param sm_file: The sm file filename
        :param directory: The directory of the song, containing the audio and sm files
        """
        self.directory = directory
        self.folder_name = os.path.basename(directory)
        self.name = name

        # Creating and using an ogg file for the audio for now because that's what Resonite supports.
        self.audio_file_path = self.get_ogg_audio_file_path(original_audio_file_path=os.path.join(self.directory, audio_file))
        self.audio_file_name = os.path.basename(self.audio_file_path)

        self.sm_file_name = sm_file
        self.sm_file_contents = sm_file_contents
        self.title = ""
        self.artist = ""
        self.bpms: List[List[float]] = []  # eg [[0.0, 137.7], [4.0, 138.0]]
        self.min_bpm = 0.0
        self.max_bpm = 0.0

        self.charts: List[Chart] = []
        self.single_charts: List[Chart] = []
        self.double_charts: List[Chart] = []

        self.chart_guids: List[str] = []
        self.duration: float = 0.0  # Song duration in seconds
        self.duration_str: str = ""
        self.sample_start = 0.0
        self.sample_length = 0.0
        self.offset = 0.0
        self.song_id = song_id or str(uuid4())
        self.detect_jacket()
        self.detect_background()
        self.loaded = False
        return

    @property
    def is_single_song(self) -> bool:
        return len(self.single_charts) > 0

    @property
    def is_double_song(self) -> bool:
        return len(self.double_charts) > 0

    def get_ogg_audio_file_path(self, original_audio_file_path: str) -> str:
        # If it's already an ogg file, return its path
        if original_audio_file_path.endswith('.ogg'):
            return original_audio_file_path

        # Check if an ogg file with the same base name already exists in the directory
        base_name = os.path.splitext(os.path.basename(original_audio_file_path))[0]
        ogg_file_path = os.path.join(self.directory, f"{base_name}.ogg")
        if os.path.exists(ogg_file_path):
            return ogg_file_path

        # Convert the audio to ogg format and save it in the directory with the same base name
        try:
            if original_audio_file_path.endswith('.mp3'):
                audio = AudioSegment.from_mp3(original_audio_file_path)
            elif original_audio_file_path.endswith('.wav'):
                audio = AudioSegment.from_wav(original_audio_file_path)
            else:
                logger.info(f"Unsupported audio format for conversion in {self.directory}")
                return original_audio_file_path  # Return original if format is unsupported

            # Export the audio as an ogg file
            audio.export(ogg_file_path, format='ogg')
            logger.info(f"Converted {original_audio_file_path} to {ogg_file_path}")

        except Exception as e:
            logger.error(f"Failed to convert {original_audio_file_path} to ogg: {e}")
            return original_audio_file_path  # Return original path if conversion fails

        return ogg_file_path

    def create_sample_ogg(self):
        # Check if the sample.ogg already exists
        sample_path = os.path.join(self.directory, 'reso-dmx-sample.ogg')
        if os.path.exists(sample_path):
            # logger.info(f"A sample file already exists for the song {self.name} in {self.directory}")
            return

        try:
            # Load the original audio file
            if self.audio_file_path.endswith('.mp3'):
                original_audio = AudioSegment.from_mp3(self.audio_file_path)
            elif self.audio_file_path.endswith('.ogg'):
                original_audio = AudioSegment.from_ogg(self.audio_file_path)
            elif self.audio_file_path.endswith('.wav'):
                original_audio = AudioSegment.from_wav(self.audio_file_path)
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
            logger.error(f"Failed to create sample for {self.name} in {self.directory} due to error: {e}")

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

    def set_duration(self, duration: float):
        self.duration = duration
        self.duration_str = format_seconds(duration)


    def load_song_info_and_charts_from_sm_file_contents(self, sm_file_contents: str):
        """
        This needs to be called explicitly after the Song object is created, in order to populate the charts list.
        :param sm_file_path:
        :return:
        """

        try:
            title, artist, sample_start, sample_length, bpms, stops, charts, offset = self.parse_sm_file_contents(sm_file_contents)
        except Exception as e:
            logger.error(f"Song {self.name} simfile in {self.directory} could not be read: {str(e)}")
            return

        self.title = title
        self.artist = artist
        self.sample_start = sample_start
        self.sample_length = sample_length if sample_length > 0 else 10.0
        self.offset = offset

        self.bpms = bpms

        if len(self.bpms) == 0:
            logger.warning(f"Song {self.name} in {self.directory} has no BPMs - skipping.")
            return

        self.loaded = True

        self.min_bpm = min(bpm[1] for bpm in self.bpms)
        self.max_bpm = max(bpm[1] for bpm in self.bpms)

        self.stops = stops

        self.duration = self.get_audio_duration(audio_file_path=self.audio_file_path)
        self.set_duration(self.duration)

        self.create_sample_ogg()

        # Remove charts that are not mode "dance-single" (eg. "dance-double")
        self.charts = [chart for chart in charts if (chart.is_single_chart or chart.is_double_chart)]

        # Sort the charts by difficulty level ascending
        self.charts.sort(key=lambda x: x.difficulty_level)

        self.chart_guids = [chart.chart_id for chart in self.charts]

    def load_charts_from_sm_file(self):
        """
        This needs to be called explicitly after the Song object is created, in order to populate the charts list.
        """
        sm_file_path = os.path.join(self.directory, self.sm_file_name)

        try:
            self.sm_file_contents = read_file_with_encodings(sm_file_path)
        except Exception as e:
            logger.error(f"Failed to load {self.sm_file_name} in {self.directory}: {e}")
            return

        self.load_song_info_and_charts_from_sm_file_contents(sm_file_contents=self.sm_file_contents)

        return

    @staticmethod
    def parse_sm_file_contents(sm_file_contents: str) -> tuple[
        str, str, float, float, list[Any] | list[tuple[float, ...]], list[Any] | list[tuple[float, ...]], list[
            Chart], float]:
        """
        Parses the contents of an SM file provided as a string.
        :param sm_file_contents: The contents of the SM file as a single string.
        :return: Tuple containing title, artist, sample start, sample length, BPMs, stops, charts, and offset.
        """

        song_data = simfile.loads(string=sm_file_contents, strict=False)
        title = song_data.title
        artist = song_data.artist
        bpms_str = song_data.bpms.strip()
        bpms = [list(map(float, bpm.split("="))) for bpm in bpms_str.split(",")]
        sample_length = float(song_data.samplelength) if song_data.samplelength else 15.0
        sample_start = float(song_data.samplestart) if song_data.samplestart else 0.0

        if song_data.stops:
            stops_str = song_data.stops.strip()
            stops = [tuple(map(float, stop.split("="))) for stop in stops_str.split(",") if stop]
        else:
            stops = []

        offset = float(song_data.offset) if song_data.offset else 0.0

        def parse_string_to_list(input_string):
            groups = [group.strip().splitlines() for group in input_string.split(',')]
            return groups


        charts = []
        for chart_data in song_data.charts.data:
            measures = parse_string_to_list(chart_data.notes)
            chart = Chart(
                chart_id=None,
                mode=chart_data.stepstype,
                difficulty_name=chart_data.difficulty,
                difficulty_level=int(chart_data.meter),
                measures=measures
            )
            charts.append(chart)

        return title, artist, sample_start, sample_length, bpms, stops, charts, offset

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