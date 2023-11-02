from flask import Flask, jsonify, abort, make_response
from modules.Music.Group import find_songs
import logging

app = Flask(__name__)

# Load songs into groups using the provided method.
root_directory = './songs'
groups = find_songs(root_directory)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info(f"Found {sum(len(group.songs) for group in groups)} songs in {len(groups)} groups.")


@app.route('/groups/count', methods=['GET'])
def get_group_count():
    """
    Example: /groups/count
    """
    return str(len(groups))


@app.route('/groups/<int:group_idx>/name', methods=['GET'])
def get_group_name(group_idx):
    """
    Example: /groups/0/name
    """
    if group_idx >= len(groups) or group_idx < 0:
        abort(404)
    return groups[group_idx].name


@app.route('/groups/<int:group_idx>/songs/count', methods=['GET'])
def get_song_count(group_idx):
    """
    Example: /groups/0/songs/count
    """
    if group_idx >= len(groups) or group_idx < 0:
        abort(404)
    return str(len(groups[group_idx].songs))


@app.route('/groups/<int:group_idx>/songs/<int:song_idx>/title', methods=['GET'])
def get_song_title(group_idx, song_idx):
    """
    Example: /groups/0/songs/0/title
    """
    if group_idx >= len(groups) or group_idx < 0:
        abort(404)
    group = groups[group_idx]
    if song_idx >= len(group.songs) or song_idx < 0:
        abort(404)
    return group.songs[song_idx].title


@app.route('/groups/<int:group_idx>/songs/<int:song_idx>/artist', methods=['GET'])
def get_song_artist(group_idx, song_idx):
    """
    Example: /groups/0/songs/0/artist
    """
    if group_idx >= len(groups) or group_idx < 0:
        abort(404)
    group = groups[group_idx]
    if song_idx >= len(group.songs) or song_idx < 0:
        abort(404)
    return group.songs[song_idx].artist


@app.route('/groups/<int:group_idx>/songs/<int:song_idx>/details', methods=['GET'])
def get_song_details(group_idx, song_idx):
    """
    Example: /groups/0/songs/0/details
    """
    if group_idx >= len(groups) or group_idx < 0:
        abort(404)
    group = groups[group_idx]
    if song_idx >= len(group.songs) or song_idx < 0:
        abort(404)
    song = group.songs[song_idx]
    details = [
        song.title,
        song.artist,
        f"BPM Range: {song.min_bpm} - {song.max_bpm}",
        f"Duration: {song.duration:.2f} seconds"
    ]
    return '\n'.join(details)



@app.errorhandler(404)
def not_found(error):
    return make_response("Error: Not Found", 404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5730)
