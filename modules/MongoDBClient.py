# MongoDBClient.py

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.server_api import ServerApi
from modules.Config import Config
from typing import List, Dict, Any, Optional
import logging
import datetime
from bson import ObjectId
from modules.utils.Loggers import configure_console_logger


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
            [("user_id", ASCENDING), ("chart_guid", ASCENDING)], unique=True
        )
        self.settings_collection.create_index("user_id", unique=True)

    def add_score(self, user_id: str, chart_guid: str, percentage_score: float, timestamp: int) -> None:
        """
        Adds or updates a score for a specific user and chart. If a score already exists, it is overwritten.

        :param user_id: The ID of the user.
        :param chart_guid: The GUID of the chart.
        :param percentage_score: The percentage score achieved by the user.
        :param timestamp: The UNIX timestamp of when the score was achieved.
        """
        score_entry = {
            "user_id": user_id,
            "chart_guid": chart_guid,
            "percentage_score": percentage_score,
            "timestamp": timestamp
        }
        self.scores_collection.update_one(
            {"user_id": user_id, "chart_guid": chart_guid},  # Match criteria
            {"$set": score_entry},  # Update or set the score entry
            upsert=True  # Create a new entry if none exists
        )
        logger.info(f"Score for user '{user_id}' on chart '{chart_guid}' updated or added.")

    def _limit_scores(self, user_id: str, chart_guid: str) -> None:
        """
        Limits the number of stored scores for a user and chart to the latest 10 entries.

        :param user_id: The ID of the user.
        :param chart_guid: The GUID of the chart.
        """
        scores = list(self.scores_collection.find(
            {"user_id": user_id, "chart_guid": chart_guid}
        ).sort("timestamp", -1))
        if len(scores) > 10:
            for score in scores[10:]:
                self.scores_collection.delete_one({"_id": score["_id"]})

    def get_user_scores_bulk(self, user_id: str, chart_ids: List[str]) -> Dict[str, Optional[float]]:
        """
        Fetches scores for a user across multiple chart IDs in a single query.

        This method optimizes performance by querying the database only once to retrieve
        scores for multiple charts instead of making separate queries for each chart.

        :param user_id: The ID of the user.
        :param chart_ids: A list of chart GUIDs for which to fetch scores.
        :return: A dictionary mapping chart IDs to their percentage scores (or None if no score is found).

        Example:
        Input:
            user_id = "player1"
            chart_ids = ["chart1", "chart2", "chart3"]

        MongoDB Query:
            Finds all documents in the `scores_collection` where:
            - "user_id" matches the given `user_id`.
            - "chart_guid" is in the list of provided `chart_ids`.

            Projection:
            - Only retrieves the "chart_guid" and "percentage_score" fields to optimize the query.

        Output:
            {
                "chart1": 98.75,  # Found score
                "chart2": None,   # No score found
                "chart3": 87.50   # Found score
            }
        """
        # Perform a query to find scores for the given user and chart IDs
        results = self.scores_collection.find(
            {"user_id": user_id, "chart_guid": {"$in": chart_ids}},  # Match criteria
            {"chart_guid": 1, "percentage_score": 1}  # Projection to include only required fields
        )

        # Initialize a dictionary with all chart IDs set to None (default for missing scores)
        scores = {chart_id: None for chart_id in chart_ids}

        # Iterate through query results and map chart IDs to their respective scores
        for result in results:
            # For each result, update the score for the corresponding chart ID
            scores[result["chart_guid"]] = result.get("percentage_score", None)

        return scores

    def get_user_score(self, user_id: str, chart_guid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user's score information for a specific chart.

        :param user_id: The ID of the user.
        :param chart_guid: The GUID of the chart.
        :return: A dictionary containing the score information, or None if not found.
        """
        result = self.scores_collection.find_one({"user_id": user_id, "chart_guid": chart_guid})
        return serialize_mongo_document(result)

    def delete_scores_for_user(self, user_id: str) -> None:
        """
        Deletes all scores for a specific user from the database.

        :param user_id: The ID of the user whose scores should be deleted.
        """
        result = self.scores_collection.delete_many({"user_id": user_id})
        logger.info(f"Deleted {result.deleted_count} scores for user '{user_id}'.")

    def delete_scores_for_chart(self, chart_guid: str) -> None:
        """
        Deletes all scores for a specific chart from the database.

        :param chart_guid: The GUID of the chart whose scores should be deleted.
        """
        result = self.scores_collection.delete_many({"chart_guid": chart_guid})
        logger.info(f"Deleted {result.deleted_count} scores for chart '{chart_guid}'.")


    def delete_scores_for_charts(self, chart_guids: List[str]) -> None:
        """
        Deletes all scores for a list of charts from the database.

        :param chart_guids: A list of chart GUIDs whose scores should be deleted.
        """
        result = self.scores_collection.delete_many({"chart_guid": {"$in": chart_guids}})
        logger.info(f"Deleted {result.deleted_count} scores for {len(chart_guids)} charts.")


    def get_top_scores(self, chart_guid: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the top scores for a specific chart by percentage score, ensuring each entry is the best score for a unique user.

        :param chart_guid: The GUID of the chart.
        :param limit: The maximum number of top scores to return.
        :return: A list of dictionaries containing the top scores, sorted by percentage score in descending order.
        """
        pipeline = [
            {"$match": {"chart_guid": chart_guid}},
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
                          note_scroll_direction: str,
                          combo_text_position: int,
                          judgement_text_position: int,
                          background_filter: int,
                          ) -> None:
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
            "background_filter": background_filter,
            "combo_text_position": combo_text_position,
            "judgement_text_position": judgement_text_position,
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
    configure_console_logger()
    logger = logging.getLogger(__name__)
    config = Config('../config.ini')
    db_client = MongoDBClient(config)

    # Example usage: Setting user settings
    db_client.set_user_settings(
        user_id="player1",
        scroll_speed=1.5,
        noteskin="default",
        controller_type="Standard",
        controller_buttons={
            "button_0": "A",
            "button_1": "B",
            "button_2": "X",
            "button_3": "Y",
        },
        visual_timing_offset=0.05,
        judgement_timing_offset=0.1,
        height_of_notes_area=500,
        arrow_x_axis_spacing=50,
        note_scroll_direction="up"
    )
    logger.info(f"User settings for 'player1': {db_client.get_user_settings('player1')}")

    # Delete all scores for sample users before adding new scores
    db_client.delete_scores_for_user("player1")
    db_client.delete_scores_for_user("player2")

    # Example usage: Adding scores
    chart_guid = "example-chart-guid-1"
    now = int(datetime.datetime.now().timestamp())

    # Add or overwrite scores for the same chart and user
    db_client.add_score(user_id="player1", chart_guid=chart_guid, percentage_score=98.5, timestamp=now)
    db_client.add_score(user_id="player1", chart_guid=chart_guid, percentage_score=95.0, timestamp=now - 60)  # Overwrites previous
    db_client.add_score(user_id="player2", chart_guid=chart_guid, percentage_score=96.5, timestamp=now - 120)
    db_client.add_score(user_id="player2", chart_guid=chart_guid, percentage_score=97.0, timestamp=now - 180)  # Overwrites previous

    # Retrieve scores for a user
    user_score = db_client.get_user_score(user_id="player1", chart_guid=chart_guid)
    logger.info(f"Retrieved score for 'player1': {user_score}")

    # Retrieve top scores for the chart
    top_scores = db_client.get_top_scores(chart_guid=chart_guid, limit=5)
    logger.info(f"Top scores for chart '{chart_guid}': {top_scores}")

    logger.info("Sample MongoDBClient usage completed.")