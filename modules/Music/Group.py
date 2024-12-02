from typing import List
import logging
from modules.Music.Song import Song
import os
from modules.utils.FileUtils import read_file_with_encodings

from modules.SQLiteConnector import SQLiteConnector

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


def find_songs(root_directory: str, sqlite_db_connector: SQLiteConnector) -> List[Group]:
    root_directory = os.path.abspath(root_directory)
    groups = []
    valid_sm_file_paths = set()
    valid_song_directory_paths = set()
    valid_group_directory_paths = set()

    for group_dir in os.listdir(root_directory):
        if group_dir == "ignore":  # Skip ignored folders
            continue

        group_directory_path = os.path.join(root_directory, group_dir)
        if os.path.isdir(group_directory_path):
            group = Group(group_dir)
            group_guid = sqlite_db_connector.insert_group(name=group.name, directory_path=group_directory_path)
            valid_group_directory_paths.add(group_directory_path)

            for song_dir in os.listdir(group_directory_path):
                song_path = os.path.join(group_directory_path, song_dir)
                if os.path.isdir(song_path):
                    song_files = os.listdir(song_path)
                    audio_file = next(
                        (f for f in song_files if f.endswith(('.ogg', '.mp3')) and "reso-dmx-sample" not in f), None)
                    sm_file = next((f for f in song_files if f.endswith('.sm')), None)

                    if audio_file and sm_file:
                        song = Song(name=song_dir, audio_file=audio_file, directory=song_path, id=len(group.songs),
                                    sm_file=sm_file)
                        song.load_charts_from_sm_file()

                        if not song.loaded:
                            continue

                        sm_file_path = os.path.join(song.directory, song.sm_file_name)
                        valid_sm_file_paths.add(sm_file_path)

                        last_modified = os.path.getmtime(sm_file_path)
                        stored_last_modified = sqlite_db_connector.get_sm_file_last_modified(sm_file_path)

                        if stored_last_modified:
                            # Since the song already exists in the db, we can get the GUID from the db
                            song_guid = sqlite_db_connector.get_song_guid_by_directory_path(song.directory)
                            # The song already exists in the db
                            # Need to update the sm file in the db if it has changed
                            if last_modified > stored_last_modified:
                                sqlite_db_connector.insert_or_update_sm_file(sm_file_path, song.sm_file_contents)
                                # Insert charts into the database
                                for chart in song.charts:
                                    sqlite_db_connector.insert_chart(song_guid,
                                                                     sm_file_path,
                                                                     chart.difficulty_name,
                                                                     chart.difficulty_level)
                            else:
                                # The song already exists in the db and the sm file has not changed
                                pass
                        else:
                            # The song does not exist in the db yet, we need to insert it and generate a GUID for it
                            song_guid = sqlite_db_connector.insert_song(group_guid, song.name, song.directory)
                            # Insert charts into the database
                            for chart in song.charts:
                                sqlite_db_connector.insert_chart(song_guid,
                                                                 sm_file_path,
                                                                 chart.difficulty_name,
                                                                 chart.difficulty_level)
                            sqlite_db_connector.insert_or_update_sm_file(sm_file_path, song.sm_file_contents)

                        valid_song_directory_paths.add(song.directory)
                        group.songs.append(song)

            groups.append(group)
            logger.info(f"Processed group '{group.name}' with {len(group.songs)} songs.")

    # Clean up orphaned records
    sqlite_db_connector.cleanup_orphaned_records(valid_group_directory_paths,
                                                 valid_song_directory_paths,
                                                 valid_sm_file_paths)
    return groups
