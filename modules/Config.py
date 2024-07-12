import configparser
import os

class Config:
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        if not os.path.exists(self.config_file_path):
            raise Exception(f"Config file not found at {self.config_file_path}")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)

        self.mongodb_uri = self.config.get('database', 'uri')
        self.sample_audio_filename = self.config.get('io', 'sample_audio_filename')