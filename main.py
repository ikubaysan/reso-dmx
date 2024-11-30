from modules.FlaskAppHandler import FlaskAppHandler
from modules.Config import Config
import time
import os
import logging
from modules.utils.Loggers import configure_console_logger


if __name__ == '__main__':
    configure_console_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting Flask app...")
    config = Config(config_file_path="config.ini")

    root_directory = os.path.abspath("./songs/")
    #root_directory = os.path.abspath("./songs/ignore/")

    flask_app = FlaskAppHandler(config=config,
                                host="0.0.0.0",
                                port=5731,
                                root_directory=root_directory
                                )
    flask_app.run()