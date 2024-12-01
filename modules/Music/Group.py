from typing import List
import logging
from modules.Music.Song import Song
import os
logger = logging.getLogger(__name__)

class Group:
    def __init__(self, name: str):
        """
        :param name: The name of the group
        """
        self.name = name
        self.songs: List[Song] = []
        self.song_count = 0

    def add_song(self, song_dir: str, audio_file: str, sm_file: str, song_path: str):
        song = Song(song_dir, audio_file, song_path, self.song_count, sm_file)

        song.load_charts_from_sm_file()

        if not song.loaded:
            return

        if song.duration == 0:
            logger.warning(f"Song {song.name} has a duration of 0 seconds - skipping.")
            return

        self.songs.append(song)
        self.song_count += 1


def find_songs(root_directory: str) -> List[Group]:
    root_directory = os.path.abspath(root_directory)
    groups = []

    for group_dir in os.listdir(root_directory):
        # If the folder name is "ignore", skip it
        if group_dir == "ignore":
            continue

        group_path = os.path.join(root_directory, group_dir)

        if os.path.isdir(group_path):
            group = Group(group_dir)
            for song_dir in os.listdir(group_path):
                song_path = os.path.join(group_path, song_dir)

                if os.path.isdir(song_path):
                    song_files = os.listdir(song_path)
                    audio_file = next((f for f in song_files if f.endswith(('.ogg', '.mp3')) and "reso-dmx-sample" not in f), None)
                    sm_file = next((f for f in song_files if f.endswith('.sm')), None)

                    if audio_file and sm_file:
                        group.add_song(song_dir, audio_file, sm_file, song_path)

            groups.append(group)
            logger.info(f"Found {group.song_count} songs in group '{group.name}'")

    return groups