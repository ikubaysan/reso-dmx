from flask import Flask, jsonify, abort, make_response, send_from_directory
from modules.Music.Group import find_songs
import logging
import os

class FlaskAppHandler:
    def __init__(self, host='0.0.0.0', port=5731, root_directory='./songs'):
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

    def validate_indices(self, group_idx, song_idx=None):
        if group_idx >= len(self.groups) or group_idx < 0:
            abort(404)
        group = self.groups[group_idx]
        if song_idx is not None:
            if song_idx >= len(group.songs) or song_idx < 0:
                abort(404)
            return group, group.songs[song_idx]
        return group

    def setup_routes(self):
        @self.app.route('/groups/count', methods=['GET'])
        def get_group_count():
            return str(len(self.groups))

        @self.app.route('/groups/<int:group_idx>/name', methods=['GET'])
        def get_group_name(group_idx):
            group = self.validate_indices(group_idx)
            return group.name

        @self.app.route('/groups/<int:group_idx>/songs/count', methods=['GET'])
        def get_song_count(group_idx):
            group = self.validate_indices(group_idx)
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
                f"BPM Range: {song.min_bpm} - {song.max_bpm}" if song.min_bpm != song.max_bpm else f"BPM: {song.min_bpm}",
                f"Duration: {song.duration:.2f} seconds"
            ]
            return '\n'.join(details)

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/jacket', methods=['GET'])
        def get_song_jacket(group_idx, song_idx):
            group, song = self.validate_indices(group_idx, song_idx)
            return send_from_directory(directory=self.root_directory, path=f"{group.name}/{song.folder_name}/{song.jacket}")

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/background', methods=['GET'])
        def get_song_background(group_idx, song_idx):
            group, song = self.validate_indices(group_idx, song_idx)
            return send_from_directory(directory=self.root_directory, path=f"{group.name}/{song.folder_name}/{song.background}")

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/sample', methods=['GET'])
        def get_song_sample(group_idx, song_idx):
            group, song = self.validate_indices(group_idx, song_idx)
            return send_from_directory(directory=self.root_directory, path=f"{group.name}/{song.folder_name}/reso-dmx-sample.ogg")

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/audio', methods=['GET'])
        def get_song_audio(group_idx, song_idx):
            group, song = self.validate_indices(group_idx, song_idx)
            return send_from_directory(directory=self.root_directory, path=f"{group.name}/{song.folder_name}/{song.audio_file}")

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

        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/<int:chart_idx>/measures', methods=['GET'])
        def get_chart_measures(group_idx, song_idx, chart_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            if chart_idx >= len(song.charts) or chart_idx < 0:
                abort(404)
            chart = song.charts[chart_idx]
            return jsonify(chart.measures)

        @self.app.errorhandler(404)
        def not_found(error):
            return make_response("Error: Not Found", 404)

    def run(self):
        self.app.run(host=self.host, port=self.port)


if __name__ == "__main__":
    # Change the working directory to the root of the project before running this.
    app = FlaskAppHandler(root_directory=os.path.abspath("../songs"))
    app.run()
