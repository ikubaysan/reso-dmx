from typing import List, Tuple, Dict, Any

class Chart:
    def __init__(self, mode: str, difficulty_name: str, difficulty_level: int, notes: List[str]):
        """
        :param mode: "dance-single" or "dance-double"
        :param difficulty_name: "Beginner", "Easy", "Medium", "Hard", "Challenge"
        :param difficulty_level: An integer from 1 to 20
        :param notes: A list of strings, each string representing a row of notes. Eg ["0000", "0000"...]
        """
        self.mode = mode
        self.difficulty_name = difficulty_name
        self.difficulty_level = difficulty_level
        self.notes = notes
