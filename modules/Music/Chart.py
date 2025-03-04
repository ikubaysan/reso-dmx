from typing import List, Tuple, Dict, Any
from modules.Music.Beat import Beat
from typing import Optional
from uuid import uuid4

class Chart:
    def __init__(self,
                 chart_id: Optional[str],
                 mode: str,
                 difficulty_name: str,
                 difficulty_level: int,
                 measures: list[list[[str]]] = None,
                 note_count: int = 0,
                 beats_as_resonite_string: str = "",
                 ):
        """
        :param mode: "dance-single" or "dance-double"
        :param difficulty_name: "Beginner", "Easy", "Medium", "Hard", "Challenge"
        :param difficulty_level: An integer from 1 to 20
        :param measures: A list of lists of strings, each string representing a measure containing notes. For example:
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

        self.note_count = note_count
        self.beats: List[Beat] = []
        self.beats_as_resonite_string = beats_as_resonite_string
        self.chart_id = chart_id or str(uuid4())
