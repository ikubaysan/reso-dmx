# MongoDBClient.py

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.server_api import ServerApi
from modules.Config import Config
from typing import List, Dict, Any, Optional
import logging
import datetime
from bson import ObjectId


logger = logging.getLogger(__name__)


def serialize_mongo_document(doc):
    """
    Recursively convert ObjectId in a MongoDB document to string.
    """
    if isinstance(doc, dict):
        return {key: serialize_mongo_document(value) for key, value in doc.items()}
    elif isinstance(doc, list):
        return [serialize_mongo_document(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    else:
        return doc


class MongoDBClient:
    def __init__(self, config: Config):
        """
        Initialize the DatabaseClient with a MongoDB connection.

        :param config: Config object containing the database URI and settings.
        """
        uri = config.mongodb_uri
        # Connect to the MongoDB deployment with API version 1
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        try:
            self.client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(e)
        self.db = self.client['stepmania_game']
        self.scores_collection = self.db['scores']
        self.settings_collection = self.db['settings']
        self._create_indexes()

    def _create_indexes(self) -> None:
        """
        Create necessary indexes for the collections to optimize queries.
        """
        self.scores_collection.create_index(
            [('user_id', ASCENDING), ('group_id', ASCENDING), ('song_id', ASCENDING), ('chart_id', ASCENDING)]
        )
        self.scores_collection.create_index(
            [('group_id', ASCENDING), ('song_id', ASCENDING), ('chart_id', ASCENDING), ('percentage_score', ASCENDING)]
        )
        self.settings_collection.create_index('user_id', unique=True)

    def add_score(self, user_id: str, group_id: str, song_id: str, chart_id: str,
                  percentage_score: float, timestamp: int) -> None:
        """
        Add a new score entry to the database. limit_scores() will then be called,
        so we keep only the latest 10 scores per chart per user.

        :param user_id: The user_id of the player.
        :param group_id: The ID of the group.
        :param song_id: The ID of the song.
        :param chart_id: The ID of the chart.
        :param percentage_score: The percentage score.
        :param timestamp: The time the score was achieved, as an epoch integer.
        """
        score_entry = {
            "user_id": user_id,
            "group_id": group_id,
            "song_id": song_id,
            "chart_id": chart_id,
            "percentage_score": percentage_score,
            "timestamp": timestamp
        }
        self.scores_collection.insert_one(score_entry)
        self._limit_scores(user_id, group_id, song_id, chart_id)

    def _limit_scores(self, user_id: str, group_id: str, song_id: str, chart_id: str) -> None:
        """
        Limit the number of scores for a specific chart and user to the latest 10.

        :param user_id: The user_id of the player.
        :param group_id: The ID of the group.
        :param song_id: The ID of the song.
        :param chart_id: The ID of the chart.
        """
        # Find the scores sorted by timestamp in descending order
        scores = list(self.scores_collection.find(
            {"user_id": user_id, "group_id": group_id, "song_id": song_id, "chart_id": chart_id}
        ).sort("timestamp", -1))

        # If there are more than 10 scores, delete the oldest ones
        if len(scores) > 10:
            for score in scores[10:]:
                self.scores_collection.delete_one({"_id": score["_id"]})

    def get_user_score(self, user_id: str, group_id: str, song_id: str, chart_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user's score information for a specific chart.

        :param user_id: The user_id of the player.
        :param group_id: The ID of the group.
        :param song_id: The ID of the song.
        :param chart_id: The ID of the chart.
        :return: A dictionary containing the score information or None if not found.
        """
        result = self.scores_collection.find_one(
            {"user_id": user_id, "group_id": group_id, "song_id": song_id, "chart_id": chart_id})
        return serialize_mongo_document(result)

    def get_top_scores(self, group_id: str, song_id: str, chart_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the top scores for a specific chart by percentage score, ensuring each entry is the best score for a unique user.

        :param group_id: The ID of the group.
        :param song_id: The ID of the song.
        :param chart_id: The ID of the chart.
        :param limit: The maximum number of top scores to return.
        :return: A list of dictionaries containing the top scores, descending by percentage score.
        """
        pipeline = [
            {"$match": {"group_id": group_id, "song_id": song_id, "chart_id": chart_id}},
            {"$sort": {"user_id": ASCENDING, "percentage_score": DESCENDING}},
            {"$group": {
                "_id": "$user_id",
                "best_score": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$best_score"}},
            {"$sort": {"percentage_score": DESCENDING}},
            {"$limit": limit}
        ]

        return list(self.scores_collection.aggregate(pipeline))

    def set_user_settings(self, user_id: str, scroll_speed: float, noteskin: str,
                          controller_type: str, controller_buttons: Dict[str, str],
                          visual_timing_offset: float, judgement_timing_offset: float,
                          height_of_notes_area: float, arrow_x_axis_spacing: float,
                          note_scroll_direction: str) -> None:
        """
        Set or update a user's settings.

        :param user_id: The user_id of the player.
        :param scroll_speed: The scroll speed setting.
        :param noteskin: The noteskin setting.
        :param controller: The controller type.
        :param controller_buttons: Mapping of controller buttons (e.g., button_0, button_1).
        :param visual_timing_offset: Visual timing offset for display.
        :param judgement_timing_offset: Timing offset for judgement.
        :param height_of_notes_area: Height of the notes area.
        :param arrow_x_axis_spacing: Spacing of arrows on the x-axis.
        :param note_scroll_direction: Scroll direction for notes.
        """
        settings = {
            "user_id": user_id,
            "scroll_speed": scroll_speed,
            "noteskin": noteskin,
            "controller_type": controller_type,
            "controller_buttons": controller_buttons,
            "visual_timing_offset": visual_timing_offset,
            "judgement_timing_offset": judgement_timing_offset,
            "height_of_notes_area": height_of_notes_area,
            "arrow_x_axis_spacing": arrow_x_axis_spacing,
            "note_scroll_direction": note_scroll_direction,
        }
        self.settings_collection.update_one({"user_id": user_id}, {"$set": settings}, upsert=True)

    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user's settings.

        :param user_id: The user_id of the player.
        :return: A dictionary containing the user's settings or None if not found.
        """
        result = self.settings_collection.find_one({"user_id": user_id})
        return serialize_mongo_document(result)


if __name__ == "__main__":
    config = Config('../config.ini')
    db_client = MongoDBClient(config)

    # Example usage
    db_client.set_user_settings("player1", 1.5, 0.1, "default")
    logger.info(db_client.get_user_settings("player1"))

    now = int(datetime.datetime.now().timestamp())
    db_client.add_score("player1", "group1", "song1", "chart1", 99.5, now)
    db_client.add_score("player1", "group1", "song1", "chart1", 89.5, now)
    db_client.add_score("player2", "group1", "song1", "chart1", 94.5, now)
    db_client.add_score("player2", "group1", "song1", "chart1", 96.0, now)
    db_client.add_score("player3", "group1", "song1", "chart1", 85.0, now)
    db_client.add_score("player4", "group1", "song1", "chart1", 75.0, now)
    db_client.add_score("player5", "group1", "song1", "chart1", 65.0, now)
    db_client.add_score("player5", "group1", "song1", "chart1", 70.0, now)

    logger.info(db_client.get_top_scores("group1", "song1", "chart1", limit=5))
