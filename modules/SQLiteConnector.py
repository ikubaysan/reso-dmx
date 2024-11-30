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
        """
        Initializes required tables in the database.
        """
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
        return guid

    def insert_song(self, group_guid: str, name: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT guid FROM songs WHERE group_guid = ? AND name = ?", (group_guid, name))
        row = cursor.fetchone()
        if row:
            guid = row[0]
        else:
            guid = str(uuid4())
            cursor.execute("INSERT INTO songs (guid, group_guid, name) VALUES (?, ?, ?)", (guid, group_guid, name))
            self.conn.commit()
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
        return guid

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

    def cleanup_orphaned_records(self, valid_group_guids: List[str], valid_song_guids: List[str]) -> None:
        cursor = self.conn.cursor()

        # Delete songs not associated with valid groups
        if valid_group_guids:
            placeholders = ','.join('?' * len(valid_group_guids))
            cursor.execute(f"DELETE FROM songs WHERE group_guid NOT IN ({placeholders})", valid_group_guids)
        else:
            # If no valid groups, delete all songs
            cursor.execute("DELETE FROM songs")

        # Delete charts not associated with valid songs
        if valid_song_guids:
            placeholders = ','.join('?' * len(valid_song_guids))
            cursor.execute(f"DELETE FROM charts WHERE song_guid NOT IN ({placeholders})", valid_song_guids)
        else:
            # If no valid songs, delete all charts
            cursor.execute("DELETE FROM charts")

        # Delete groups not in valid_group_guids
        if valid_group_guids:
            placeholders = ','.join('?' * len(valid_group_guids))
            cursor.execute(f"DELETE FROM groups WHERE guid NOT IN ({placeholders})", valid_group_guids)
        else:
            # If no valid groups, delete all groups
            cursor.execute("DELETE FROM groups")

        self.conn.commit()

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
