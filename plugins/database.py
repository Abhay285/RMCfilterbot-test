from pymongo import MongoClient
from config import DATABASE_URL, DATABASE_NAME

class Database:
    def __init__(self):
        self._client = MongoClient(DATABASE_URL)
        self.db = self._client[DATABASE_NAME]
        self.col = self.db["Posts"]

    def insert_post(self, data):
        return self.col.insert_one(data)

    def search_posts(self, query):
        return self.col.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort("score", -1)

# Global database instance
database = Database()
