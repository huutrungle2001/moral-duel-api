"""
Leaderboard Update Job

Updates leaderboard cache for performance optimization
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.utils.database import get_db

logger = logging.getLogger(__name__)


async def update_leaderboard_cache_job():
    """
    Update leaderboard cache for fast queries
    
    Flow:
    1. Calculate rankings for different time periods (daily, weekly, all-time)
    2. Store in leaderboard_cache table
    3. Handle ties in rankings
    4. Clean old cache entries
    """
    try:
        logger.info("Starting leaderboard cache update...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        now = datetime.utcnow()
        
        # Calculate all-time leaderboard
        await _update_leaderboard(db, "all_time", None, now)
        
        # Calculate weekly leaderboard (last 7 days)
        week_ago = now - timedelta(days=7)
        await _update_leaderboard(db, "weekly", week_ago, now)
        
        # Calculate daily leaderboard (last 24 hours)
        day_ago = now - timedelta(days=1)
        await _update_leaderboard(db, "daily", day_ago, now)
        
        # Clean old cache entries (older than 1 hour)
        old_threshold = now - timedelta(hours=1)
        deleted = await db.leaderboardcache.delete_many(
            where={
                "updated_at": {
                    "lt": old_threshold
                }
            }
        )
        
        logger.info(
            f"✓ Leaderboard cache updated: "
            f"Cleaned {deleted} old entries"
        )
        
    except Exception as e:
        logger.error(f"Leaderboard cache update failed: {str(e)}", exc_info=True)


async def _update_leaderboard(
    db,
    period: str,
    start_date: datetime | None,
    end_date: datetime
) -> int:
    """
    Update leaderboard for a specific time period
    
    Args:
        db: Database connection
        period: "all_time", "weekly", or "daily"
        start_date: Start of period (None for all-time)
        end_date: End of period
        
    Returns:
        Number of users in leaderboard
    """
    try:
        # Build reward query for time period
        reward_where = {
            "status": "completed"
        }
        
        if start_date:
            reward_where["completed_at"] = {
                "gte": start_date,
                "lte": end_date
            }
        
        # Get all users who have earned rewards in this period
        # Group by user and sum their points
        rewards = await db.reward.find_many(
            where=reward_where,
            include={"user": True}
        )
        
        # Calculate points per user
        user_points: Dict[int, Dict[str, Any]] = {}
        
        for reward in rewards:
            user_id = reward.user_id
            if user_id not in user_points:
                user_points[user_id] = {
                    "user_id": user_id,
                    "username": reward.user.username if reward.user else "Unknown",
                    "points": 0,
                    "wins": 0,
                    "cases_participated": 0
                }
            
            user_points[user_id]["points"] += reward.amount
            
            # Count wins (winning_vote rewards)
            if reward.reason == "winning_vote":
                user_points[user_id]["wins"] += 1
            
            # Count participation
            if reward.reason in ["winning_vote", "participation"]:
                user_points[user_id]["cases_participated"] += 1
        
        # Sort by points (descending)
        sorted_users = sorted(
            user_points.values(),
            key=lambda x: x["points"],
            reverse=True
        )
        
        # Assign ranks (handle ties)
        current_rank = 1
        previous_points = None
        
        for i, user_data in enumerate(sorted_users):
            if previous_points is not None and user_data["points"] < previous_points:
                current_rank = i + 1
            
            user_data["rank"] = current_rank
            previous_points = user_data["points"]
        
        # Clear old cache for this period
        await db.leaderboardcache.delete_many(
            where={"period": period}
        )
        
        # Insert new cache entries
        cache_entries = []
        for user_data in sorted_users[:100]:  # Top 100 only
            cache_entries.append({
                "user_id": user_data["user_id"],
                "rank": user_data["rank"],
                "points": user_data["points"],
                "period": period,
                "updated_at": end_date
            })
        
        if cache_entries:
            await db.leaderboardcache.create_many(
                data=cache_entries
            )
        
        logger.info(
            f"✓ Updated {period} leaderboard: {len(cache_entries)} users cached"
        )
        
        return len(cache_entries)
        
    except Exception as e:
        logger.error(f"Failed to update {period} leaderboard: {str(e)}")
        return 0


async def calculate_user_rank(
    db,
    user_id: int,
    period: str = "all_time"
) -> Dict[str, Any]:
    """
    Calculate a specific user's rank
    
    Args:
        db: Database connection
        user_id: User ID
        period: Time period
        
    Returns:
        User rank information
    """
    try:
        # Check cache first
        cached = await db.leaderboardcache.find_first(
            where={
                "user_id": user_id,
                "period": period
            },
            order={"updated_at": "desc"}
        )
        
        if cached:
            # Check if cache is fresh (< 15 minutes old)
            age = datetime.utcnow() - cached.updated_at
            if age < timedelta(minutes=15):
                return {
                    "rank": cached.rank,
                    "points": cached.points,
                    "period": period,
                    "cached": True
                }
        
        # Calculate live if not cached
        user = await db.user.find_unique(
            where={"id": user_id}
        )
        
        if not user:
            return {
                "rank": None,
                "points": 0,
                "period": period,
                "error": "User not found"
            }
        
        # Count users with more points
        if period == "all_time":
            users_above = await db.user.count(
                where={
                    "total_points": {
                        "gt": user.total_points
                    }
                }
            )
        else:
            # For time-based periods, need to sum rewards
            # This is more complex, use cache or return approximate
            users_above = 0
        
        rank = users_above + 1
        
        return {
            "rank": rank,
            "points": user.total_points,
            "period": period,
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate user rank: {str(e)}")
        return {
            "rank": None,
            "points": 0,
            "error": str(e)
        }
