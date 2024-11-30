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
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS songs (
                guid TEXT PRIMARY KEY,
                group_guid TEXT NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY(group_guid) REFERENCES groups(guid)
            );

            CREATE TABLE IF NOT EXISTS charts (
                guid TEXT PRIMARY KEY,
                song_guid TEXT NOT NULL,
                difficulty_name TEXT NOT NULL,
                difficulty_level INTEGER NOT NULL,
                FOREIGN KEY(song_guid) REFERENCES songs(guid)
            );

            CREATE TABLE IF NOT EXISTS sm_files (
                path TEXT PRIMARY KEY,
                last_modified REAL NOT NULL,
                content TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def insert_group(self, name: str) -> str:
        """
        Inserts a new group into the database or returns the existing GUID.

        :param name: Name of the group.
        :return: GUID of the inserted or existing group.
        """
        cursor = self.conn.cursor()
        guid = str(uuid4())

        # Use INSERT OR IGNORE to avoid duplicates
        cursor.execute("""
            INSERT OR IGNORE INTO groups (guid, name)
            VALUES (?, ?)
        """, (guid, name))

        # Retrieve the existing or newly inserted GUID
        cursor.execute("SELECT guid FROM groups WHERE name = ?", (name,))
        guid = cursor.fetchone()[0]
        self.conn.commit()
        return guid

    def insert_song(self, group_guid: str, name: str) -> str:
        """
        Inserts a new song into the database.

        :param group_guid: GUID of the associated group.
        :param name: Name of the song.
        :return: GUID of the inserted song.
        """
        guid = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO songs (guid, group_guid, name) VALUES (?, ?, ?)", (guid, group_guid, name))
        self.conn.commit()
        return guid

    def insert_chart(self, song_guid: str, difficulty_name: str, difficulty_level: int) -> str:
        """
        Inserts a new chart into the database.

        :param song_guid: GUID of the associated song.
        :param difficulty_name: Name of the difficulty.
        :param difficulty_level: Level of the difficulty.
        :return: GUID of the inserted chart.
        """
        guid = str(uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO charts (guid, song_guid, difficulty_name, difficulty_level) VALUES (?, ?, ?, ?)",
            (guid, song_guid, difficulty_name, difficulty_level)
        )
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

    def cleanup_orphaned_records(self, valid_groups: List[str], valid_songs: List[str]) -> None:
        """
        Deletes orphaned groups and songs that no longer exist.

        :param valid_groups: List of valid group GUIDs.
        :param valid_songs: List of valid song GUIDs.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM songs WHERE group_guid NOT IN (SELECT guid FROM groups WHERE guid IN (?))",
                       (",".join(valid_groups),))
        cursor.execute("DELETE FROM charts WHERE song_guid NOT IN (SELECT guid FROM songs WHERE guid IN (?))",
                       (",".join(valid_songs),))
        cursor.execute("DELETE FROM groups WHERE guid NOT IN (?)", (",".join(valid_groups),))
        self.conn.commit()

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
