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
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS songs (
                guid TEXT PRIMARY KEY,
                group_guid TEXT NOT NULL,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                FOREIGN KEY(group_guid) REFERENCES groups(guid),
                UNIQUE(group_guid, name)
            );

            CREATE TABLE IF NOT EXISTS charts (
                guid TEXT PRIMARY KEY,
                song_guid TEXT NOT NULL,
                difficulty_name TEXT NOT NULL,
                difficulty_level INTEGER NOT NULL,
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

    def insert_group(self, name: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM groups WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            guid = row[0]
        else:
            guid = str(uuid4())
            cursor.execute("INSERT INTO groups (guid, name) VALUES (?, ?)", (guid, name))
            self.conn.commit()
            logger.info(f"New group added: {name} (GUID: {guid})")
        return guid

    def insert_song(self, group_guid: str, name: str, path: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM songs WHERE path = ?", (path,))
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
            cursor.execute("INSERT INTO songs (guid, group_guid, name, path) VALUES (?, ?, ?, ?)",
                           (guid, group_guid, name, path))
            self.conn.commit()
            logger.info(f"New song added: {name} (GUID: {guid})")
        return guid

    def insert_chart(self, song_guid: str, difficulty_name: str, difficulty_level: int) -> str:
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
                INSERT INTO charts (guid, song_guid, difficulty_name, difficulty_level)
                VALUES (?, ?, ?, ?)
            """, (guid, song_guid, difficulty_name, difficulty_level))
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

    def get_song_guid_by_path(self, path: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM songs WHERE path = ?", (path,))
        row = cursor.fetchone()
        return row[0] if row else None

    def cleanup_orphaned_records(self, valid_group_guids: List[str], valid_song_guids: List[str],
                                 valid_sm_file_paths: set, valid_song_paths: set):
        cursor = self.conn.cursor()

        # Delete songs whose paths are no longer in the filesystem
        cursor.execute("SELECT guid, name, path FROM songs")
        all_songs = cursor.fetchall()
        orphaned_song_guids = []
        for song in all_songs:
            song_guid, song_name, song_path = song
            if song_path not in valid_song_paths:
                logger.info(f"Deleting orphaned song: Name: {song_name}, Path: {song_path}")
                orphaned_song_guids.append(song_guid)
        if orphaned_song_guids:
            placeholders = ','.join('?' * len(orphaned_song_guids))
            cursor.execute(f"DELETE FROM songs WHERE guid IN ({placeholders})", orphaned_song_guids)

        # Delete charts not associated with valid songs
        if valid_song_guids:
            placeholders = ','.join('?' * len(valid_song_guids))
            cursor.execute(f"SELECT guid, song_guid FROM charts WHERE song_guid NOT IN ({placeholders})",
                           valid_song_guids)
        else:
            cursor.execute("SELECT guid, song_guid FROM charts")
        orphaned_charts = cursor.fetchall()
        for chart in orphaned_charts:
            logger.info(f"Deleting orphaned chart: GUID: {chart[0]}, Song GUID: {chart[1]}")
        if orphaned_charts:
            chart_guids = [chart[0] for chart in orphaned_charts]
            placeholders = ','.join('?' * len(chart_guids))
            cursor.execute(f"DELETE FROM charts WHERE guid IN ({placeholders})", chart_guids)

        # Delete groups not in valid_group_guids
        if valid_group_guids:
            placeholders = ','.join('?' * len(valid_group_guids))
            cursor.execute(f"SELECT guid, name FROM groups WHERE guid NOT IN ({placeholders})", valid_group_guids)
        else:
            cursor.execute("SELECT guid, name FROM groups")
        orphaned_groups = cursor.fetchall()
        for group in orphaned_groups:
            logger.info(f"Deleting orphaned group: GUID: {group[0]}, Name: {group[1]}")
        if orphaned_groups:
            group_guids = [group[0] for group in orphaned_groups]
            placeholders = ','.join('?' * len(group_guids))
            cursor.execute(f"DELETE FROM groups WHERE guid IN ({placeholders})", group_guids)

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

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
