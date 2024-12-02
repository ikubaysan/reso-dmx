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
        if not os.path.isdir(group_directory_path):
            logger.warning(f"Skipping non-directory '{group_dir}'.")
            continue

        group = Group(group_dir)
        group_guid = sqlite_db_connector.insert_group(name=group.name, directory_path=group_directory_path)
        valid_group_directory_paths.add(group_directory_path)

        # Initialize per group lists
        sm_file_paths = []
        song_directory_paths = []
        song_info_list = []

        for song_dir in os.listdir(group_directory_path):
            song_path = os.path.join(group_directory_path, song_dir)
            if os.path.isdir(song_path):
                song_files = os.listdir(song_path)
                audio_file = next(
                    (f for f in song_files if f.endswith(('.ogg', '.mp3')) and "reso-dmx-sample" not in f), None)
                sm_file = next((f for f in song_files if f.endswith('.sm')), None)

                if audio_file and sm_file:
                    sm_file_path = os.path.join(song_path, sm_file)
                    sm_file_paths.append(sm_file_path)
                    song_directory_paths.append(song_path)
                    # Store info for later processing
                    song_info_list.append({'song_dir': song_dir,
                                           'audio_file': audio_file,
                                           'song_path': song_path,
                                           'sm_file': sm_file,
                                           'sm_file_path': sm_file_path})

        # Batch fetch SM files and songs from the database
        sm_files_from_db = sqlite_db_connector.get_sm_files_for_paths(sm_file_paths)
        songs_from_db = sqlite_db_connector.get_songs_by_directory_paths(song_directory_paths)

        for song_info in song_info_list:
            song_dir = song_info['song_dir']
            audio_file = song_info['audio_file']
            song_path = song_info['song_path']
            sm_file = song_info['sm_file']
            sm_file_path = song_info['sm_file_path']

            last_modified = os.path.getmtime(sm_file_path)
            stored_sm_file_entry = sm_files_from_db.get(sm_file_path)

            if stored_sm_file_entry:
                stored_last_modified = stored_sm_file_entry['last_modified']
                if last_modified <= stored_last_modified:
                    # SM file has not changed, load content from db
                    sm_file_contents = stored_sm_file_entry['content']
                    # logger.info(f"Loading SM file from database for song '{song_dir}'.")
                    song = Song(name=song_dir, audio_file=audio_file, directory=song_path,
                                id=len(group.songs), sm_file=sm_file,
                                sm_file_contents=sm_file_contents)
                else:
                    # SM file has changed, read from filesystem
                    try:
                        sm_file_contents = read_file_with_encodings(sm_file_path)
                    except Exception as e:
                        logger.error(f"Failed to load {sm_file_path}: {e}")
                        continue
                    logger.info(f"SM file has changed, loading from filesystem for song '{song_dir}'.")
                    # Update the SM file in the database
                    sqlite_db_connector.insert_or_update_sm_file(sm_file_path, sm_file_contents)
                    song = Song(name=song_dir,
                                audio_file=audio_file,
                                directory=song_path,
                                id=len(group.songs),
                                sm_file=sm_file,
                                sm_file_contents=sm_file_contents)
            else:
                # SM file not in db, read from filesystem
                try:
                    sm_file_contents = read_file_with_encodings(sm_file_path)
                except Exception as e:
                    logger.error(f"Failed to load {sm_file_path}: {e}")
                    continue
                logger.info(f"SM file not in database, loading from filesystem for song '{song_dir}'.")
                # Insert the SM file into the database
                sqlite_db_connector.insert_or_update_sm_file(sm_file_path, sm_file_contents)
                song = Song(name=song_dir, audio_file=audio_file, directory=song_path,
                            id=len(group.songs), sm_file=sm_file,
                            sm_file_contents=sm_file_contents)

            # Load charts from SM file contents
            song.load_charts_from_sm_file_contents(song.sm_file_contents)

            if not song.loaded:
                continue

            # Check if song exists in the database
            song_guid = songs_from_db.get(song.directory)
            if not song_guid:
                # Song not in db, insert song
                song_guid = sqlite_db_connector.insert_song(group_guid, song.name, song.directory)
                # Insert charts into the database
                for chart in song.charts:
                    sqlite_db_connector.insert_chart(song_guid,
                                                     sm_file_path,
                                                     chart.difficulty_name,
                                                     chart.difficulty_level)
                # SM file already inserted or updated earlier

            valid_sm_file_paths.add(sm_file_path)
            valid_song_directory_paths.add(song.directory)
            group.songs.append(song)

        groups.append(group)
        logger.info(f"Processed group '{group.name}' with {len(group.songs)} songs.")

    # Clean up orphaned records
    sqlite_db_connector.cleanup_orphaned_records(valid_group_directory_paths,
                                                 valid_song_directory_paths,
                                                 valid_sm_file_paths)
    return groups

