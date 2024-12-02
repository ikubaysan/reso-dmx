import sqlite3
import os
import time
from typing import Optional, List, Dict
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class SQLiteConnector:
    def __init__(self, db_path: str):
        """
        Initializes the SQLiteConnector.

        :param db_path: Path to the SQLite database file.
        """
        self.db_path = os.path.abspath(db_path)
        self.conn = None
        self.create_db_if_not_exists()

    def create_db_if_not_exists(self):
        """
        Creates the SQLite database file if it does not exist and initializes tables.
        """
        if not os.path.exists(self.db_path):
            logger.info(f"Database does not exist. Creating new database at {self.db_path}.")
        self.conn = sqlite3.connect(self.db_path)
        self.initialize_tables()

    def initialize_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS groups (
                guid TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                directory_path TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS songs (
                guid TEXT PRIMARY KEY,
                group_guid TEXT NOT NULL,
                name TEXT NOT NULL,
                directory_path TEXT NOT NULL UNIQUE,
                FOREIGN KEY(group_guid) REFERENCES groups(guid),
                UNIQUE(group_guid, name)
            );

            CREATE TABLE IF NOT EXISTS charts (
                guid TEXT PRIMARY KEY,
                song_guid TEXT NOT NULL,
                path TEXT NOT NULL,
                difficulty_name TEXT NOT NULL,
                difficulty_level INTEGER NOT NULL,
                note_count INTEGER,
                FOREIGN KEY(song_guid) REFERENCES songs(guid),
                UNIQUE(song_guid, difficulty_name, difficulty_level)
            );

            CREATE TABLE IF NOT EXISTS sm_files (
                path TEXT PRIMARY KEY,
                last_modified REAL NOT NULL,
                content TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def insert_group(self, name: str, directory_path: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM groups WHERE directory_path = ?", (directory_path,))
        row = cursor.fetchone()
        if row:
            guid = row[0]
        else:
            guid = str(uuid4())
            cursor.execute("INSERT INTO groups (guid, name, directory_path) VALUES (?, ?, ?)", (guid, name, directory_path))
            self.conn.commit()
            logger.info(f"New group added: {directory_path} (GUID: {guid})")
        return guid

    def get_sm_files_for_paths(self, paths: List[str]) -> Dict[str, Dict]:
        cursor = self.conn.cursor()
        if not paths:
            return {}
        placeholders = ','.join(['?'] * len(paths))
        query = f"SELECT path, last_modified, content FROM sm_files WHERE path IN ({placeholders})"
        cursor.execute(query, paths)
        rows = cursor.fetchall()
        return {row[0]: {'last_modified': row[1], 'content': row[2]} for row in rows}

    def get_songs_by_directory_paths(self, paths: List[str]) -> Dict[str, str]:
        cursor = self.conn.cursor()
        if not paths:
            return {}
        placeholders = ','.join(['?'] * len(paths))
        query = f"SELECT directory_path, guid FROM songs WHERE directory_path IN ({placeholders})"
        cursor.execute(query, paths)
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    def get_song_guid_by_directory_path(self, directory_path: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM songs WHERE directory_path = ?", (directory_path,))
        row = cursor.fetchone()
        return row[0] if row else None


    def insert_song(self, group_guid: str, name: str, directory_path: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM songs WHERE directory_path = ?", (directory_path,))
        row = cursor.fetchone()
        if row:
            guid = row[0]
            # Update the song's name and group_guid if necessary
            cursor.execute("""
                UPDATE songs SET name = ?, group_guid = ? WHERE guid = ?
            """, (name, group_guid, guid))
            self.conn.commit()
        else:
            guid = str(uuid4())
            cursor.execute("INSERT INTO songs (guid, group_guid, name, directory_path) VALUES (?, ?, ?, ?)",
                           (guid, group_guid, name, directory_path))
            self.conn.commit()
            logger.info(f"New song added: {name} (GUID: {guid})")
        return guid

    def insert_chart(self, song_guid: str, sm_file_path: str, difficulty_name: str, difficulty_level: int) -> str:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT guid FROM charts
            WHERE song_guid = ? AND difficulty_name = ? AND difficulty_level = ?
        """, (song_guid, difficulty_name, difficulty_level))
        row = cursor.fetchone()
        if row:
            guid = row[0]
        else:
            guid = str(uuid4())
            cursor.execute("""
                INSERT INTO charts (guid, song_guid, path, difficulty_name, difficulty_level)
                VALUES (?, ?, ?, ?, ?)
            """, (guid, song_guid, sm_file_path, difficulty_name, difficulty_level))
            self.conn.commit()
            logger.info(f"New chart added: {difficulty_name} (Level: {difficulty_level}, GUID: {guid})")
        return guid

    def delete_charts_by_song_guid(self, song_guid: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM charts WHERE song_guid = ?", (song_guid,))
        self.conn.commit()
        logger.info(f"Deleted all charts for song GUID: {song_guid}")

    def insert_or_update_sm_file(self, path: str, content: str) -> None:
        """
        Inserts or updates an SM file record in the database.

        :param path: Path of the SM file.
        :param content: Content of the SM file.
        """
        last_modified = os.path.getmtime(path)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sm_files (path, last_modified, content)
            VALUES (?, ?, ?)
            ON CONFLICT(path)
            DO UPDATE SET last_modified = excluded.last_modified, content = excluded.content;
        """, (path, last_modified, content))
        self.conn.commit()

    def get_sm_file_last_modified(self, path: str) -> Optional[float]:
        """
        Retrieves the last modified timestamp of an SM file from the database.

        :param path: Path of the SM file.
        :return: Last modified timestamp or None if the file is not in the database.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_modified FROM sm_files WHERE path = ?", (path,))
        row = cursor.fetchone()
        return row[0] if row else None

    def cleanup_orphaned_records(self,
                                 valid_group_directory_paths: set,
                                 valid_song_directory_paths: set,
                                 valid_sm_file_paths: set):
        cursor = self.conn.cursor()

        # Delete songs not in valid_song_directory_paths
        cursor.execute("SELECT guid, name, directory_path FROM songs")
        all_songs = cursor.fetchall()
        orphaned_song_guids = []
        for song in all_songs:
            song_guid, song_name, song_directory_path = song
            if song_directory_path not in valid_song_directory_paths:
                logger.info(f"Deleting orphaned song: Name: {song_name}, Path: {song_directory_path}")
                orphaned_song_guids.append(song_guid)
        if orphaned_song_guids:
            placeholders = ','.join('?' * len(orphaned_song_guids))
            cursor.execute(f"DELETE FROM songs WHERE guid IN ({placeholders})", tuple(orphaned_song_guids))

        # Delete charts associated with the songs that were deleted
        if orphaned_song_guids:
            placeholders = ','.join('?' * len(orphaned_song_guids))
            cursor.execute(f"DELETE FROM charts WHERE song_guid IN ({placeholders})", tuple(orphaned_song_guids))
            logger.info(f"Deleted all charts for {len(orphaned_song_guids)} orphaned songs.")

        # Delete groups not in valid_group_directory_paths
        if valid_group_directory_paths:
            placeholders = ','.join('?' * len(valid_group_directory_paths))
            cursor.execute(
                f"SELECT guid, name, directory_path FROM groups WHERE directory_path NOT IN ({placeholders})",
                tuple(valid_group_directory_paths))
        else:
            cursor.execute("SELECT guid, name, directory_path FROM groups")
        orphaned_groups = cursor.fetchall()
        for group in orphaned_groups:
            logger.info(f"Deleting orphaned group: GUID: {group[0]}, Name: {group[1]}, Directory Path: {group[2]}")
        if orphaned_groups:
            group_guids = [group[0] for group in orphaned_groups]
            placeholders = ','.join('?' * len(group_guids))
            cursor.execute(f"DELETE FROM groups WHERE guid IN ({placeholders})", tuple(group_guids))

        # Delete SM files that are no longer in the filesystem
        cursor.execute("SELECT path FROM sm_files")
        db_sm_files = {row[0] for row in cursor.fetchall()}
        orphaned_sm_files = db_sm_files - valid_sm_file_paths
        for sm_file in orphaned_sm_files:
            logger.info(f"Deleting orphaned SM file: Path: {sm_file}")
        if orphaned_sm_files:
            placeholders = ','.join('?' * len(orphaned_sm_files))
            cursor.execute(f"DELETE FROM sm_files WHERE path IN ({placeholders})", tuple(orphaned_sm_files))

        self.conn.commit()
        logger.info("Completed cleanup of orphaned records.")

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
