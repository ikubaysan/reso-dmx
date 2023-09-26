from modules.utils.FileUtils import find_songs
from modules.utils.Loggers import configure_console_logger
import logging

configure_console_logger()
logger = logging.getLogger(__name__)


def main():
    root_directory = './songs'
    groups = find_songs(root_directory)

    total_songs = sum(len(group.songs) for group in groups)

    logger.info(f"Found {total_songs} songs in {len(groups)} groups.")
    for group in groups:
        logger.info(f"Group: {group.name}, Songs: {len(group.songs)}")
        for song in group.songs:
            logger.info(f"Song: {song.name}, Duration: {song.duration} seconds")

    return


if __name__ == "__main__":
    main()
