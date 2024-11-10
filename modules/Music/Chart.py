from typing import List, Tuple, Dict, Any
from modules.Music.Beat import Beat

class Chart:
    def __init__(self, mode: str, difficulty_name: str, difficulty_level: int, measures: List[str]):
        """
        :param mode: "dance-single" or "dance-double"
        :param difficulty_name: "Beginner", "Easy", "Medium", "Hard", "Challenge"
        :param difficulty_level: An integer from 1 to 20
        :param measures: A list of strings, each string representing a measure containing notes. For example:
        [
            ...
            05 = {list: 16} ['0010', '0000', '0000', '0000', '1000', '0000', '0000', '0000', '0010', '0000', '0000', '0000', '0100', '0001', '0100', '0001']
            06 = {list: 8} ['0100', '0000', '0010', '0000', '1000', '0000', '0100', '1000']
            08 = {list: 4} ['1000', '0010', '1000', '0101']
            07 = {list: 16} ['0001', '0000', '0000', '0000', '0100', '0000', '0000', '0000', '0001', '0000', '0000', '0000', '1000', '0010', '1000', '0010']
            04 = {list: 4} ['0000', '0000', '0000', '0000']
            ...
        ]

        05 is a measure with 16 beats.
        06 is a measure with 8 beats.
        08 is a measure with 4 beats.

        """
        self.mode = mode
        self.difficulty_name = difficulty_name
        self.difficulty_level = difficulty_level
        self.measures = measures

        self.note_count = 0
        self.beats: List[Beat] = []
        self.beats_as_resonite_string = ""
