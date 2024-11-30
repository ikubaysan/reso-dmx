from flask import Flask, jsonify, abort, make_response, url_for, send_from_directory, request
from modules.Music.Group import Group
from modules.Music.Song import Song
from modules.Music.Group import find_songs
from modules.Music.Beat import precalculate_beats, get_beats_as_resonite_string
from modules.Config import Config
from typing import List, Tuple, Optional
import logging
import os
from modules.utils.Loggers import configure_console_logger

logger = logging.getLogger(__name__)
from modules.DatabaseClient import DatabaseClient
class FlaskAppHandler:
    def __init__(self, config: Config, host='0.0.0.0', base_url="http://servers.ikubaysan.com", port=5731, root_directory='./songs'):
        self.app = Flask(__name__)
        self.host = host
        self.base_url = base_url
        self.config = config
        self.db_client = DatabaseClient(self.config)
        self.port = port
        self.root_directory = root_directory
        self.groups = find_songs(self.root_directory)
        self.file_guid_map = {}  # Dictionary to store GUID to file path mapping
        self.setup_routes()
        self.setup_logging()
        self.force_always_precalculate_beats = False
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

    def setup_db_routes(self):
        """
        Set up API routes for interacting with the database.
        """

        @self.app.route('/db/score', methods=['GET', 'POST'])
        def score():
            """
            Add or retrieve a score entry.
            - POST Example URL: /db/score?user_id=player1&group_id=group1&song_id=song1&chart_id=chart1&percentage_score=95.5&timestamp=1699999999
            - GET Example URL: /db/score?user_id=player1&group_id=group1&song_id=song1&chart_id=chart1
            """
            if request.method == 'POST':
                # Adding a score
                user_id = request.args.get('user_id')
                group_id = request.args.get('group_id')
                song_id = request.args.get('song_id')
                chart_id = request.args.get('chart_id')
                percentage_score = float(request.args.get('percentage_score', 0))
                timestamp = int(request.args.get('timestamp', 0))

                if not all([user_id, group_id, song_id, chart_id, percentage_score, timestamp]):
                    return make_response("Missing parameters", 400)

                self.db_client.add_score(user_id, group_id, song_id, chart_id, percentage_score, timestamp)
                return jsonify({"message": "Score added successfully"})

            elif request.method == 'GET':
                # Retrieving a score
                user_id = request.args.get('user_id')
                group_id = request.args.get('group_id')
                song_id = request.args.get('song_id')
                chart_id = request.args.get('chart_id')

                if not all([user_id, group_id, song_id, chart_id]):
                    return make_response("Missing parameters", 400)

                score = self.db_client.get_user_score(user_id, group_id, song_id, chart_id)
                if score:
                    return jsonify(score)
                else:
                    return make_response("Score not found", 404)

        @self.app.route('/db/top_scores', methods=['GET'])
        def top_scores():
            """
            Retrieve the top scores for a specific chart.
            Example URL: /db/top_scores?group_id=group1&song_id=song1&chart_id=chart1&limit=5
            """
            group_id = request.args.get('group_id')
            song_id = request.args.get('song_id')
            chart_id = request.args.get('chart_id')
            limit = int(request.args.get('limit', 10))

            if not all([group_id, song_id, chart_id]):
                return make_response("Missing parameters", 400)

            top_scores = self.db_client.get_top_scores(group_id, song_id, chart_id, limit)
            return jsonify(top_scores)


        @self.app.route('/db/settings', methods=['GET', 'POST'])
        def settings():
            """
            Set or retrieve user settings.
            - POST Example URL: /db/settings?user_id=player1&scroll_speed=1.5&noteskin=default&controller_type=0&
                                controller_button_0=A&controller_button_1=B&controller_button_2=X&
                                controller_button_3=Y&visual_timing_offset=0.05&judgement_timing_offset=0.1&
                                height_of_notes_area=500&arrow_x_axis_spacing=50&note_scroll_direction=up
            - GET Example URL: /db/settings?user_id=player1&response_type=resonite
            """
            if request.method == 'POST':
                # Setting user settings
                user_id = request.args.get('user_id')
                scroll_speed = float(request.args.get('scroll_speed', 0))
                noteskin = request.args.get('noteskin', '')
                controller_type = request.args.get('controller_type', '')
                visual_timing_offset = float(request.args.get('visual_timing_offset', 0))
                judgement_timing_offset = float(request.args.get('judgement_timing_offset', 0))
                height_of_notes_area = float(request.args.get('height_of_notes_area', 0))
                arrow_x_axis_spacing = float(request.args.get('arrow_x_axis_spacing', 0))
                note_scroll_direction = request.args.get('note_scroll_direction', '')

                # Controller buttons
                controller_buttons = {
                    "button_0": request.args.get('controller_button_0', ''),
                    "button_1": request.args.get('controller_button_1', ''),
                    "button_2": request.args.get('controller_button_2', ''),
                    "button_3": request.args.get('controller_button_3', ''),
                }

                if not user_id:
                    return make_response("Missing user_id parameter", 400)

                self.db_client.set_user_settings(
                    user_id, scroll_speed, noteskin, controller_type, controller_buttons,
                    visual_timing_offset, judgement_timing_offset,
                    height_of_notes_area, arrow_x_axis_spacing, note_scroll_direction
                )
                logger.info(f"User settings updated for {user_id}")
                return jsonify({"message": "User settings updated successfully"})

            elif request.method == 'GET':
                # Retrieving user settings
                user_id = request.args.get('user_id')
                response_type = request.args.get('response_type', 'json')  # Default to JSON response

                if not user_id:
                    return make_response("Missing user_id parameter", 400)

                settings = self.db_client.get_user_settings(user_id)
                if not settings:
                    return make_response("Settings not found", 404)

                if response_type == 'resonite':
                    # Convert settings to a resonite string
                    resonite_values = [
                        settings.get("scroll_speed", ""),
                        settings.get("visual_timing_offset", ""),
                        settings.get("judgement_timing_offset", ""),
                        settings.get("controller_type", ""),
                        settings.get("height_of_notes_area", ""),
                        settings.get("arrow_x_axis_spacing", ""),
                        settings.get("note_scroll_direction", ""),

                        settings["controller_buttons"].get("button_0", ""),
                        settings["controller_buttons"].get("button_1", ""),
                        settings["controller_buttons"].get("button_2", ""),
                        settings["controller_buttons"].get("button_3", ""),
                    ]
                    # Pad each value to 50 characters
                    # and ensure the string is 50 characters long in case the value is greater than 50 characters
                    resonite_string = ''.join(f'{str(value):<50}'[:50] for value in resonite_values)
                    return resonite_string  # Response as plain text

                logger.info(f"User settings retrieved for {user_id}")
                return jsonify(settings)

    def setup_routes(self):
        self.setup_api_routes()
        self.setup_file_routes()
        self.setup_db_routes()

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
            return f"{group.name} ({len(group.songs)} ♫)"

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

            # Check if the whole number part of the BPMs is within 1
            min_bpm_int = int(song.min_bpm)
            max_bpm_int = int(song.max_bpm)

            if abs(min_bpm_int - max_bpm_int) <= 1:
                bpm_display = f"BPM: {max_bpm_int}"  # Display the max BPM as the single BPM
            else:
                bpm_display = f"BPM Range: {min_bpm_int} - {max_bpm_int}"

            details = [
                song.title,
                song.artist,
                bpm_display,
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

            if chart.beats_as_resonite_string == "" or self.force_always_precalculate_beats:
                # We have not precalculated the beats for this chart yet
                beats, note_count = precalculate_beats(song=song, chart=chart, exclude_inactive_beats=True)
                resonite_string = get_beats_as_resonite_string(beats)

                chart.note_count = note_count
                chart.beats = beats
                chart.beats_as_resonite_string = resonite_string
            else:
                logger.info(f"Using precalculated beats for {song.name} - {chart.difficulty_name}")
                resonite_string = chart.beats_as_resonite_string

            return resonite_string

        # Route to get a chart's note count
        @self.app.route('/groups/<int:group_idx>/songs/<int:song_idx>/charts/<int:chart_idx>/note_count', methods=['GET'])
        def get_chart_note_count(group_idx, song_idx, chart_idx):
            _, song = self.validate_indices(group_idx, song_idx)
            if chart_idx >= len(song.charts) or chart_idx < 0:
                abort(404)
            return str(song.charts[chart_idx].note_count)


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
    configure_console_logger()
    config = Config(config_file_path="./config.json")
    # Change the working directory to the root of the project before running this.
    app = FlaskAppHandler(config=config, root_directory=os.path.abspath("../songs"))
    app.run()
