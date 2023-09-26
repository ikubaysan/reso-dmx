from typing import List

from modules.Song import Song


class Group:
    def __init__(self, name: str):
        self.name = name
        self.songs: List[Song] = []
