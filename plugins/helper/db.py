import motor.motor_asyncio
import time
from datetime import datetime
from config import *
from typing import List, Dict, Optional, Union, Any
import math
import os
import shutil
import subprocess
import json


class Database:
    def __init__(self, uri: str, database_name: str):
        """Initialize database connection and collections"""
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self._client[database_name]
        self.col = self.db.user
        self.channels = self.db.channels
        self.formatting = self.db.formatting
        self.admins = self.db.admins
        self.posts = self.db.posts
        self.settings = self.db.settings
        self.logs = self.db.logs

    async def initialize(self) -> None:
        """Create indexes and perform initial setup"""
        try:
            # Create indexes
            await self.channels.create_index([("group", 1)])
            await self.channels.create_index([("_id", 1), ("group", 1)], unique=True)
            await self.posts.create_index([("post_id", 1)], unique=True)
            await self.posts.create_index([("delete_after", 1)])
            await self.logs.create_index([("timestamp", -1)])
            
            print("Database indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {e}")
            raise

    # ============ User System ============ #
    def new_user(self, id: int) -> Dict[str, Any]:
        return {
            "_id": int(id),
            "file_id": None,
            "caption": None,
            "prefix": None,
            "suffix": None,
            "metadata": False,
            "metadata_code": "By :- @Madflix_Bots",
            "join_date": datetime.now(),
            "last_active": datetime.now()
        }

    async def add_user(self, id: int) -> bool:
        """Add new user if not exists"""
        try:
            if not await self.is_user_exist(id):
                user = self.new_user(id)
                await self.col.insert_one(user)
                return True
            return False
        except Exception as e:
            await self.log_error(f"add_user error: {e}")
            return False

    async def is_user_exist(self, id: int) -> bool:
        """Check if user exists"""
        try:
            user = await self.col.find_one({'_id': int(id)})
            return bool(user)
        except Exception as e:
            await self.log_error(f"is_user_exist error: {e}")
            return False

    async def total_users_count(self) -> int:
        """Get total user count"""
        try:
            return await self.col.count_documents({})
        except Exception as e:
            await self.log_error(f"total_users_count error: {e}")
            return 0

    async def get_all_users(self) -> List[Dict]:
        """Get all users"""
        try:
            return [user async for user in self.col.find({})]
        except Exception as e:
            await self.log_error(f"get_all_users error: {e}")
            return []

    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        try:
            result = await self.col.delete_many({'_id': int(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            await self.log_error(f"delete_user error: {e}")
            return False

    # ============ Admin System ============ #
    async def add_admin(self, user_id: int, admin_data: Optional[Dict] = None) -> bool:
        """Add or update admin"""
        try:
            admin_data = admin_data or {}
            admin_data.update({
                "_id": user_id,
                "is_admin": True,
                "added_at": datetime.now(),
                "last_active": datetime.now()
            })
            await self.admins.update_one(
                {"_id": user_id},
                {"$set": admin_data},
                upsert=True
            )
            return True
        except Exception as e:
            await self.log_error(f"add_admin error: {e}")
            return False

    async def remove_admin(self, user_id: int) -> bool:
        """Remove admin"""
        try:
            result = await self.admins.delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            await self.log_error(f"remove_admin error: {e}")
            return False

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        try:
            admin = await self.admins.find_one({"_id": user_id})
            return admin is not None and admin.get("is_admin", False)
        except Exception as e:
            await self.log_error(f"is_admin error: {e}")
            return False

    async def get_admin(self, user_id: int) -> Optional[Dict]:
        """Get admin data"""
        try:
            return await self.admins.find_one({"_id": user_id})
        except Exception as e:
            await self.log_error(f"get_admin error: {e}")
            return None

    async def get_all_admins(self) -> List[Dict]:
        """Get all admins"""
        try:
            return [admin async for admin in self.admins.find({"is_admin": True})]
        except Exception as e:
            await self.log_error(f"get_all_admins error: {e}")
            return []

    async def update_admin_activity(self, user_id: int) -> bool:
        """Update admin last active time"""
        try:
            await self.admins.update_one(
                {"_id": user_id},
                {"$set": {"last_active": datetime.now()}}
            )
            return True
        except Exception as e:
            await self.log_error(f"update_admin_activity error: {e}")
            return False

    # ============ Channel System ============ #
    async def add_channel(self, channel_id: int, channel_name: Optional[str] = None, group_number: int = 0) -> bool:
        """Add channel to specified group"""
        try:
            channel_id = int(channel_id)
            existing = await self.channels.find_one({"_id": channel_id})
            
            if existing:
                if existing.get("group") == group_number:
                    return False  # Already exists in same group
                # Update group if exists in different group
                await self.channels.update_one(
                    {"_id": channel_id},
                    {"$set": {"group": group_number}}
                )
                return True
            
            await self.channels.insert_one({
                "_id": channel_id,
                "name": channel_name,
                "group": group_number,
                "added_date": datetime.now(),
                "post_count": 0,
                "last_post": None
            })
            return True
        except Exception as e:
            await self.log_error(f"add_channel error: {e}")
            raise

    async def delete_channel(self, channel_id: int, group_number: int = 0) -> bool:
        """Delete channel from specified group"""
        try:
            result = await self.channels.delete_one(
                {"_id": int(channel_id), "group": group_number}
            )
            # Clean up posts referencing this channel
            await self.posts.update_many(
                {"channels.channel_id": int(channel_id)},
                {"$pull": {"channels": {"channel_id": int(channel_id)}}}
            )
            return result.deleted_count > 0
        except Exception as e:
            await self.log_error(f"delete_channel error: {e}")
            return False

    async def is_channel_exist(self, channel_id: int, group_number: int = 0) -> bool:
        """Check if channel exists in specified group"""
        try:
            channel = await self.channels.find_one(
                {"_id": int(channel_id), "group": group_number}
            )
            return channel is not None
        except Exception as e:
            await self.log_error(f"is_channel_exist error: {e}")
            return False

    async def get_all_channels(self, group_number: Optional[int] = None) -> List[Dict]:
        """Get all channels or channels in specific group"""
        try:
            if group_number is not None:
                return [channel async for channel in self.channels.find({"group": group_number})]
            return [channel async for channel in self.channels.find({})]
        except Exception as e:
            await self.log_error(f"get_all_channels error: {e}")
            return []

    async def get_channels_by_group(self, group_number: int) -> List[Dict]:
        """Get channels by group number"""
        return await self.get_all_channels(group_number)

    async def increment_channel_post(self, channel_id: int) -> bool:
        """Increment post count for channel"""
        try:
            await self.channels.update_one(
                {"_id": int(channel_id)},
                {
                    "$inc": {"post_count": 1},
                    "$set": {"last_post": datetime.now()}
                }
            )
            return True
        except Exception as e:
            await self.log_error(f"increment_channel_post error: {e}")
            return False

    # ============ Post System ============ #
    async def save_post(self, post_data: Dict) -> bool:
        """Save post data"""
        try:
            post_data["timestamp"] = datetime.now()
            await self.posts.update_one(
                {"post_id": post_data["post_id"]},
                {"$set": post_data},
                upsert=True
            )
            return True
        except Exception as e:
            await self.log_error(f"save_post error: {e}")
            return False

    async def get_post(self, post_id: int) -> Optional[Dict]:
        """Get post by ID"""
        try:
            return await self.posts.find_one({"post_id": post_id})
        except Exception as e:
            await self.log_error(f"get_post error: {e}")
            return None

    async def delete_post(self, post_id: int) -> bool:
        """Delete post by ID"""
        try:
            result = await self.posts.delete_one({"post_id": post_id})
            return result.deleted_count > 0
        except Exception as e:
            await self.log_error(f"delete_post error: {e}")
            return False

    async def get_pending_deletions(self) -> List[Dict]:
        """Get posts scheduled for deletion"""
        try:
            return await self.posts.find({
                "delete_after": {"$gt": time.time()}
            }).to_list(None)
        except Exception as e:
            await self.log_error(f"get_pending_deletions error: {e}")
            return []

    async def remove_channel_post(self, post_id: int, channel_id: int) -> bool:
        """Remove channel reference from post"""
        try:
            result = await self.posts.update_one(
                {"post_id": post_id},
                {"$pull": {"channels": {"channel_id": channel_id}}}
            )
            return result.modified_count > 0
        except Exception as e:
            await self.log_error(f"remove_channel_post error: {e}")
            return False

    async def get_post_channels(self, post_id: int) -> List[Dict]:
        """Get channels for a post"""
        try:
            post = await self.posts.find_one({"post_id": post_id})
            return post.get("channels", []) if post else []
        except Exception as e:
            await self.log_error(f"get_post_channels error: {e}")
            return []

    async def get_all_posts(self, limit: int = 0, skip: int = 0) -> List[Dict]:
        """Get all posts with pagination"""
        try:
            return [post async for post in self.posts.find({}).skip(skip).limit(limit)]
        except Exception as e:
            await self.log_error(f"get_all_posts error: {e}")
            return []

    # ============ Error Logging ============ #
    async def log_error(self, error_message: str) -> bool:
        """Log error to database"""
        try:
            await self.logs.insert_one({
                "timestamp": datetime.now(),
                "error": error_message[:1000],  # Truncate long errors
                "type": "error"
            })
            return True
        except Exception as e:
            print(f"CRITICAL: Failed to log error - {str(e)[:200]}")
            return False


# Initialize the database with connection pooling
db = Database(DB_URL, DB_NAME)

# Initialize indexes (run once at startup)
async def init_db():
    try:
        await db.initialize()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise

# Run the initialization
import asyncio
asyncio.run(init_db())
