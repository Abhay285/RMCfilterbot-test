import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI

logger = logging.getLogger(__name__)

# Initialize database
db_client = AsyncIOMotorClient(DATABASE_URI)
db = db_client["ChannelFilter"]
groups_col = db["Groups"]
users_col = db["Users"]
pending_col = db["PendingRequests"]

async def create_indexes():
    """Create database indexes at startup"""
    try:
        await pending_col.create_index("user_id", unique=True)
        await pending_col.create_index("timestamp", expireAfterSeconds=86400)  # 24h TTL
        logger.info("Database indexes created")
    except Exception as e:
        logger.error(f"Index creation error: {str(e)}")

# Group Management Functions
async def add_group(group_id, group_name, user_name, user_id, channels, f_sub, verified):
    """Add or update a group in the database"""
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
        await groups_col.update_one(
            {"_id": group_id},
            {"$set": data},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error adding group {group_id}: {str(e)}")
        return False

async def get_group(group_id):
    """Retrieve group data"""
    try:
        return await groups_col.find_one({"_id": group_id})
    except Exception as e:
        logger.error(f"Error getting group {group_id}: {str(e)}")
        return None

async def get_groups():
    """Get all groups"""
    try:
        return await groups_col.find().to_list(None)
    except Exception as e:
        logger.error(f"Error getting groups: {str(e)}")
        return []

async def update_group(group_id, new_data):
    """Update group data"""
    try:
        new_data["last_updated"] = datetime.utcnow()
        result = await groups_col.update_one(
            {"_id": group_id},
            {"$set": new_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {str(e)}")
        return False

async def delete_group(group_id):
    """Delete a group"""
    try:
        result = await groups_col.delete_one({"_id": group_id})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {str(e)}")
        return False

# User Management Functions
async def add_user(user_id, user_name):
    """Add or update a user"""
    data = {
        "_id": user_id,
        "name": user_name,
        "joined_at": datetime.utcnow(),
        "last_seen": datetime.utcnow()
    }
    try:
        await users_col.update_one(
            {"_id": user_id},
            {"$set": data},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error adding user {user_id}: {str(e)}")
        return False

async def get_users():
    """Get all users"""
    try:
        return await users_col.find().to_list(None)
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return []

async def total_users_count():
    """Get total user count"""
    try:
        return await users_col.count_documents({})
    except Exception as e:
        logger.error(f"Error counting users: {str(e)}")
        return 0

async def total_chat_count():
    """Get total group count"""
    try:
        return await groups_col.count_documents({})
    except Exception as e:
        logger.error(f"Error counting groups: {str(e)}")
        return 0

# Pending Request Functions
async def save_pending_request(user_id, chat_id, query):
    """Save a pending search request"""
    try:
        await pending_col.update_one(
            {"user_id": user_id},
            {"$set": {
                "chat_id": chat_id,
                "query": query,
                "timestamp": datetime.utcnow()
            }},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error saving pending request: {str(e)}")
        return False

async def get_pending_request(user_id):
    """Get a pending request"""
    try:
        return await pending_col.find_one({"user_id": user_id})
    except Exception as e:
        logger.error(f"Error getting pending request: {str(e)}")
        return None

async def delete_pending_request(user_id):
    """Delete a pending request"""
    try:
        await pending_col.delete_one({"user_id": user_id})
        return True
    except Exception as e:
        logger.error(f"Error deleting pending request: {str(e)}")
        return False

async def delete_after_delay(message, delay):
    """Delete message after delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass
