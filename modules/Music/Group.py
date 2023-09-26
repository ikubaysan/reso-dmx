from typing import List
from modules.Music.Song import Song
import os

class Group:
    def __init__(self, name: str):
        """
        :param name: The name of the group
        """
        self.name = name
        self.songs: List[Song] = []


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
                        song = Song(song_dir, audio_file, sm_file, song_path)
                        song.load_charts()
                        group.songs.append(song)

            groups.append(group)

    return groups