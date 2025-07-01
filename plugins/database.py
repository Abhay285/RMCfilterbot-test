from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE_URL, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._client = AsyncIOMotorClient(DATABASE_URL)
        self.db = self._client[DATABASE_NAME]
        self.col = self.db["Posts"]
        self.users_col = self.db["Users"]
        self.groups_col = self.db["Groups"]

    async def insert_post(self, data):
        return await self.col.insert_one(data)

    async def search_posts(self, query):
        return await self.col.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort("score", -1).to_list(None)

    async def find_user(self, user_id):
        return await self.users_col.find_one({"_id": user_id})

    async def update_user(self, user_id, data):
        return await self.users_col.update_one(
            {"_id": user_id},
            {"$set": data},
            upsert=True
        )

# Global async database instance
database = Database()
