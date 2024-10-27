from modules.FlaskAppHandler import FlaskAppHandler
import time
import os

if __name__ == '__main__':
    print("Starting Flask app...")
    flask_app = FlaskAppHandler(root_directory=os.path.abspath("./songs"))
    flask_app.run()