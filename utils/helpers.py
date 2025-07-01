import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI

logger = logging.getLogger(__name__)

db_client = AsyncIOMotorClient(DATABASE_URI)
db = db_client["ChannelFilter"]
groups_col = db["Groups"]
users_col = db["Users"]
pending_col = db["PendingRequests"]

async def create_indexes():
    try:
        await pending_col.create_index("user_id", unique=True)
        await pending_col.create_index("timestamp", expireAfterSeconds=86400)
        logger.info("Database indexes created")
    except Exception as e:
        logger.error(f"Index error: {e}")

async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    data = {
        "_id": group_id,
        "name": group_name,
        "user_id": user_id,
        "user_name": user_name,
        "channels": channels,
        "f_sub": f_sub,
        "verified": verified,
        "created_at": datetime.utcnow(),
        "last_updated": datetime.utcnow()
    }
    try:
        await groups_col.update_one({"_id": group_id}, {"$set": data}, upsert=True)
        return True
    except Exception as e:
        logger.error(f"Add group error: {e}")
        return False

async def get_group(group_id):
    try:
        return await groups_col.find_one({"_id": group_id})
    except Exception as e:
        logger.error(f"Get group error: {e}")
        return None

async def get_groups():
    try:
        return await groups_col.find().to_list(None)
    except Exception as e:
        logger.error(f"Get groups error: {e}")
        return []

async def update_group(group_id, new_data):
    try:
        new_data["last_updated"] = datetime.utcnow()
        result = await groups_col.update_one({"_id": group_id}, {"$set": new_data})
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Update group error: {e}")
        return False

async def add_user(user_id, user_name):
    data = {
        "_id": user_id,
        "name": user_name,
        "joined_at": datetime.utcnow(),
        "last_seen": datetime.utcnow()
    }
    try:
        await users_col.update_one({"_id": user_id}, {"$set": data}, upsert=True)
        return True
    except Exception as e:
        logger.error(f"Add user error: {e}")
        return False

async def get_users():
    try:
        return await users_col.find().to_list(None)
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return []

async def total_users_count():
    try:
        return await users_col.count_documents({})
    except Exception as e:
        logger.error(f"Count users error: {e}")
        return 0

async def total_chat_count():
    try:
        return await groups_col.count_documents({})
    except Exception as e:
        logger.error(f"Count groups error: {e}")
        return 0

async def save_pending_request(user_id, chat_id, query):
    try:
        await pending_col.update_one(
            {"user_id": user_id},
            {"$set": {"chat_id": chat_id, "query": query, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Save pending error: {e}")
        return False

async def get_pending_request(user_id):
    try:
        return await pending_col.find_one({"user_id": user_id})
    except Exception as e:
        logger.error(f"Get pending error: {e}")
        return None

async def delete_pending_request(user_id):
    try:
        await pending_col.delete_one({"user_id": user_id})
        return True
    except Exception as e:
        logger.error(f"Delete pending error: {e}")
        return False

async def delete_after_delay(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass
