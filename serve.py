from modules.FlaskAppHandler import FlaskAppHandler
import time
import os
import logging
from modules.utils.Loggers import configure_console_logger


if __name__ == '__main__':
    configure_console_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting Flask app...")
    flask_app = FlaskAppHandler(root_directory=os.path.abspath("./songs"))
    flask_app.run()