from modules.FlaskAppHandler import FlaskAppHandler
import time

if __name__ == '__main__':
    print("Starting Flask app...")
    flask_app = FlaskAppHandler()
    flask_app.run()