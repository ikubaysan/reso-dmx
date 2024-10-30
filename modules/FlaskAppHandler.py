from flask import Flask, jsonify, abort, make_response, url_for, send_from_directory
from modules.Music.Group import Group
from modules.Music.Song import Song
from modules.Music.Group import find_songs
from modules.Music.Beat import precalculate_beats, get_beats_as_resonite_string
from typing import List, Tuple, Optional
import logging
import os
import uuid

class FlaskAppHandler:
    def __init__(self, host='0.0.0.0', base_url="http://servers.ikubaysan.com", port=5731, root_directory='./songs'):
        self.app = Flask(__name__)
        self.host = host
        self.base_url = base_url
        self.port = port
        self.root_directory = root_directory
        self.groups = find_songs(self.root_directory)
        self.file_guid_map = {}  # Dictionary to store GUID to file path mapping
        self.setup_routes()
        self.setup_logging()
        self.logger.info(f"Flask server started on {self.host}:{self.port} with root directory {os.path.abspath(self.root_directory)}")
        if base_url:
            self.logger.info(f"Base URL: {self.base_url}")
        else:
            self.logger.info(f"No base URL provided. Using IP address and port.")

    def setup_logging(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger.info(f"Found {sum(len(group.songs) for group in self.groups)} songs in {len(self.groups)} groups.")

    def validate_indices(self, group_idx, song_idx=None) -> Tuple[Group, Optional[Song]]:
        if group_idx >= len(self.groups) or group_idx < 0:
            abort(404)
        group = self.groups[group_idx]
        if song_idx is not None:
            if song_idx >= len(group.songs) or song_idx < 0:
                abort(404)
            return group, group.songs[song_idx]
        return group, None

    def setup_routes(self):
        self.setup_api_routes()
        self.setup_file_routes()

        @self.app.errorhandler(404)
        def not_found(error):
            return make_response("Error: Not Found", 404)

    def setup_api_routes(self):
        @self.app.route('/groups/count', methods=['GET'])
        def get_group_count():
            return str(len(self.groups))

        @self.app.route('/groups/<int:group_idx>/name', methods=['GET'])
        def get_group_name(group_idx):
            group, _ = self.validate_indices(group_idx)
            return group.name

        @self.app.route('/groups/<int:group_idx>/songs/count', methods=['GET'])
        def get_song_count(group_idx):
            group, _ = self.validate_indices(group_idx)
            return str(len(group.songs))

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/title', methods=['GET'])
        def get_song_title(group_idx, song_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            return song.title

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/artist', methods=['GET'])
        def get_song_artist(group_idx, song_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            return song.artist

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/details', methods=['GET'])
        def get_song_details(group_idx, song_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            details = [
                song.title,
                song.artist,
                f"BPM Range: {int(song.min_bpm)} - {int(song.max_bpm)}" if song.min_bpm != song.max_bpm else f"BPM: {int(song.min_bpm)}",
                f"Duration: {song.duration_str}"
            ]
            return '\n'.join(details)

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/count', methods=['GET'])
        def get_chart_count(group_idx, song_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            return str(len(song.charts))

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/<int:chart_idx>/difficulty', methods=['GET'])
        def get_chart_difficulty(group_idx, song_idx, chart_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            return song.charts[chart_idx].difficulty_name

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/<int:chart_idx>/level', methods=['GET'])
        def get_chart_level(group_idx, song_idx, chart_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            return str(song.charts[chart_idx].difficulty_level)


        # route to get a list of difficulty levels for a song
        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/chart_levels', methods=['GET'])
        def get_chart_levels(group_idx, song_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            # A single string where each difficulty is padded with 0 to be 2 digits and separated by "|"
            return "".join([str(chart.difficulty_level).zfill(2) for chart in song.charts])

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/<int:chart_idx>/notes', methods=['GET'])
        def get_chart_measures(group_idx, song_idx, chart_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            if chart_idx >= len(song.charts) or chart_idx < 0:
                abort(404)
            chart = song.charts[chart_idx]

            beats = precalculate_beats(song=song, chart=chart, exclude_inactive_beats=True)
            resonite_string = get_beats_as_resonite_string(beats)

            return str(resonite_string)

    def setup_file_routes(self):
        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/jacket', methods=['GET'])
        def get_song_jacket(group_idx, song_idx):
            return self.generate_file_url(group_idx, song_idx, "jacket")

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/background', methods=['GET'])
        def get_song_background(group_idx, song_idx):
            return self.generate_file_url(group_idx, song_idx, "background")

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/sample', methods=['GET'])
        def get_song_sample(group_idx, song_idx):
            return self.generate_file_url(group_idx, song_idx, "sample")

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/audio', methods=['GET'])
        def get_song_audio(group_idx, song_idx):
            return self.generate_file_url(group_idx, song_idx, "audio")

        @self.app.route('/assets/<guid>/<file_type>', methods=['GET'])
        def serve_file(guid, file_type):
            if guid not in self.file_guid_map:
                abort(404)
            file_path = self.file_guid_map[guid][file_type]
            return send_from_directory(directory=self.root_directory, path=file_path)

    def generate_file_url(self, group_idx, song_idx, file_type):
        group, song = self.validate_indices(group_idx, song_idx)
        file_map = {
            "jacket": song.jacket,
            "background": song.background,
            "sample": "reso-dmx-sample.ogg",
            "audio": song.audio_file_name
        }
        file_name = file_map[file_type]
        file_path = f"{group.name}/{song.folder_name}/{file_name}"
        file_guid = song.uuid
        if file_guid not in self.file_guid_map:
            self.file_guid_map[file_guid] = {}
        self.file_guid_map[file_guid][file_type] = file_path


        if self.base_url:
            return f"{self.base_url}:{self.port}/assets/{file_guid}/{file_type}"
        else:
            return f"http://{self.host}:{self.port}/assets/{file_guid}/{file_type}"

    def run(self):
        self.app.run(host=self.host, port=self.port)


if __name__ == "__main__":
    # Change the working directory to the root of the project before running this.
    app = FlaskAppHandler(root_directory=os.path.abspath("../songs"))
    app.run()
