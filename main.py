import os
from typing import List, Tuple, Dict, Any
from mutagen.oggvorbis import OggVorbis
from mutagen.id3 import ID3
from modules.Loggers import configure_console_logger
import logging

configure_console_logger()
logger = logging.getLogger(__name__)

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


class Group:
    def __init__(self, name: str):
        self.name = name
        self.songs: List[Song] = []


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
                        chart = {
                            "mode": current_mode,
                            "difficulty_name": current_difficulty_name,
                            "difficulty_level": current_difficulty_level,
                            "notes": notes_data,
                        }
                        charts.append(chart)
                        current_difficulty_name = ""  # Reset difficulty name
                        current_difficulty_level = 0  # Reset difficulty level
                        notes_data = []  # Reset notes data
                elif line.isnumeric():
                    # Capture the notes data, which looks like 0000
                    notes_data.append(line)

    return title, artist, bpms, charts




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


def find_songs(root_directory: str) -> List[Group]:
    root_directory = os.path.abspath(root_directory)
    groups = []

    for group_dir in os.listdir(root_directory):
        group_path = os.path.join(root_directory, group_dir)

        if os.path.isdir(group_path):
            group = Group(group_dir)

            for song_dir in os.listdir(group_path):
                song_path = os.path.join(group_path, song_dir)

                if os.path.isdir(song_path):
                    song_files = os.listdir(song_path)
                    audio_file = next((f for f in song_files if f.endswith(('.ogg', '.mp3'))), None)
                    sm_file = next((f for f in song_files if f.endswith('.sm')), None)

                    if audio_file and sm_file:
                        title, artist, bpms, charts = parse_sm_file(os.path.join(song_path, sm_file))
                        song = Song(song_dir, audio_file, sm_file, song_path)
                        song.title = title
                        song.artist = artist
                        song.bpms = bpms
                        song.charts = charts
                        song.duration = get_audio_duration(os.path.join(song_path, audio_file))
                        group.songs.append(song)

            groups.append(group)

    return groups



def main():
    root_directory = './songs'
    groups = find_songs(root_directory)

    total_songs = sum(len(group.songs) for group in groups)

    logger.info(f"Found {total_songs} songs in {len(groups)} groups.")
    for group in groups:
        logger.info(f"Group: {group.name}, Songs: {len(group.songs)}")
        for song in group.songs:
            logger.info(f"Song: {song.name}, Duration: {song.duration} seconds")

    return


if __name__ == "__main__":
    main()
