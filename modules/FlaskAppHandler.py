from flask import Flask, jsonify, abort, make_response
from modules.Music.Group import find_songs
import threading
import logging
import os

class FlaskAppHandler:
    def __init__(self, host='0.0.0.0', port=5730, root_directory='./songs'):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.root_directory = root_directory
        self.groups = find_songs(self.root_directory)
        self.setup_routes()
        self.setup_logging()
        self.logger.info(f"Flask server started on {self.host}:{self.port} with root directory {os.path.abspath(self.root_directory)}")

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger.info(f"Found {sum(len(group.songs) for group in self.groups)} songs in {len(self.groups)} groups.")

    def setup_routes(self):
        @self.app.route('/groups/count', methods=['GET'])
        def get_group_count():
            return str(len(self.groups))

        @self.app.route('/groups/<int:group_idx>/name', methods=['GET'])
        def get_group_name(group_idx):
            if group_idx >= len(self.groups) or group_idx < 0:
                abort(404)
            return self.groups[group_idx].name

        @self.app.route('/groups/<int:group_idx>/songs/count', methods=['GET'])
        def get_song_count(group_idx):
            if group_idx >= len(self.groups) or group_idx < 0:
                abort(404)
            return str(len(self.groups[group_idx].songs))

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/title', methods=['GET'])
        def get_song_title(group_idx, song_idx):
            if group_idx >= len(self.groups) or group_idx < 0:
                abort(404)
            group = self.groups[group_idx]
            if song_idx >= len(group.songs) or song_idx < 0:
                abort(404)
            return group.songs[song_idx].title

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/artist', methods=['GET'])
        def get_song_artist(group_idx, song_idx):
            if group_idx >= len(self.groups) or group_idx < 0:
                abort(404)
            group = self.groups[group_idx]
            if song_idx >= len(group.songs) or song_idx < 0:
                abort(404)
            return group.songs[song_idx].artist

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/details', methods=['GET'])
        def get_song_details(group_idx, song_idx):
            if group_idx >= len(self.groups) or group_idx < 0:
                abort(404)
            group = self.groups[group_idx]
            if song_idx >= len(group.songs) or song_idx < 0:
                abort(404)
            song = group.songs[song_idx]
            details = [
                song.title,
                song.artist,
                f"BPM Range: {song.min_bpm} - {song.max_bpm}" if song.min_bpm != song.max_bpm else f"BPM: {song.min_bpm}",
                f"Duration: {song.duration:.2f} seconds"
            ]
            return '\n'.join(details)

        @self.app.errorhandler(404)
        def not_found(error):
            return make_response("Error: Not Found", 404)

    def run(self):
        self.app.run(host=self.host, port=self.port)

    def start(self):
        # Run the Flask app in a separate thread to avoid blocking
        threading.Thread(target=self.run).start()