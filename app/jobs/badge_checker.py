"""
Badge Checker Job

Checks user achievements and awards badges
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from app.utils.database import get_db

logger = logging.getLogger(__name__)


# Badge definitions
BADGES = {
    "first_win": {
        "name": "First Victory",
        "description": "Won your first case",
        "icon": "🏆",
        "bonus_points": 50
    },
    "five_wins": {
        "name": "Winning Streak",
        "description": "Won 5 cases",
        "icon": "🔥",
        "bonus_points": 200
    },
    "ten_wins": {
        "name": "Champion",
        "description": "Won 10 cases",
        "icon": "👑",
        "bonus_points": 500
    },
    "top_argument": {
        "name": "Master Debater",
        "description": "Had an argument in the top 3",
        "icon": "💬",
        "bonus_points": 100
    },
    "top_argument_3x": {
        "name": "Persuasion Expert",
        "description": "Had 3 arguments in the top 3",
        "icon": "🎯",
        "bonus_points": 300
    },
    "active_participant": {
        "name": "Active Member",
        "description": "Participated in 20 cases",
        "icon": "⭐",
        "bonus_points": 150
    },
    "dedicated_voter": {
        "name": "Dedicated Voter",
        "description": "Voted in 50 cases",
        "icon": "🗳️",
        "bonus_points": 250
    },
    "early_adopter": {
        "name": "Early Adopter",
        "description": "Joined during beta",
        "icon": "🚀",
        "bonus_points": 100
    },
    "wallet_connected": {
        "name": "Blockchain Ready",
        "description": "Connected Neo wallet",
        "icon": "🔗",
        "bonus_points": 50
    }
}


async def check_badges_job():
    """
    Check users for badge achievements
    
    Flow:
    1. Get all users
    2. Check each badge criteria
    3. Award badges to qualifying users
    4. Award bonus points
    5. Prevent duplicate awards
    """
    try:
        logger.info("Starting badge checker job...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        # Get all users
        users = await db.user.find_many(
            include={
                "badges": True
            }
        )
        
        total_awarded = 0
        
        for user in users:
            try:
                badges_awarded = await _check_user_badges(db, user)
                total_awarded += badges_awarded
            except Exception as e:
                logger.error(f"Failed to check badges for user {user.id}: {str(e)}")
                continue
        
        logger.info(
            f"✓ Badge checking completed: {total_awarded} new badges awarded"
        )
        
    except Exception as e:
        logger.error(f"Badge checker job failed: {str(e)}", exc_info=True)


async def _check_user_badges(db, user) -> int:
    """
    Check and award badges for a specific user
    
    Args:
        db: Database connection
        user: User object with badges relation
        
    Returns:
        Number of badges awarded
    """
    awarded_count = 0
    existing_badge_names = {badge.badge_name for badge in user.badges}
    
    # Count user's rewards by type
    rewards = await db.reward.find_many(
        where={
            "user_id": user.id,
            "status": "completed"
        }
    )
    
    # Count wins
    wins = sum(1 for r in rewards if r.reason == "winning_vote")
    
    # Count top arguments
    top_args = sum(1 for r in rewards if r.reason == "top_argument")
    
    # Count participation
    participation = sum(1 for r in rewards if r.reason in ["winning_vote", "participation"])
    
    # Count votes
    votes = await db.uservote.count(
        where={"user_id": user.id}
    )
    
    # Check each badge criteria
    badges_to_award = []
    
    # Win-based badges
    if wins >= 1 and "first_win" not in existing_badge_names:
        badges_to_award.append("first_win")
    
    if wins >= 5 and "five_wins" not in existing_badge_names:
        badges_to_award.append("five_wins")
    
    if wins >= 10 and "ten_wins" not in existing_badge_names:
        badges_to_award.append("ten_wins")
    
    # Argument-based badges
    if top_args >= 1 and "top_argument" not in existing_badge_names:
        badges_to_award.append("top_argument")
    
    if top_args >= 3 and "top_argument_3x" not in existing_badge_names:
        badges_to_award.append("top_argument_3x")
    
    # Participation badges
    if participation >= 20 and "active_participant" not in existing_badge_names:
        badges_to_award.append("active_participant")
    
    if votes >= 50 and "dedicated_voter" not in existing_badge_names:
        badges_to_award.append("dedicated_voter")
    
    # Wallet connection badge
    if user.neo_wallet_address and "wallet_connected" not in existing_badge_names:
        badges_to_award.append("wallet_connected")
    
    # Award badges
    for badge_name in badges_to_award:
        badge_info = BADGES.get(badge_name)
        if not badge_info:
            continue
        
        try:
            # Create badge record
            await db.badge.create(
                data={
                    "user_id": user.id,
                    "badge_name": badge_name,
                    "earned_at": datetime.utcnow()
                }
            )
            
            # Award bonus points
            if badge_info["bonus_points"] > 0:
                await db.user.update(
                    where={"id": user.id},
                    data={
                        "total_points": {
                            "increment": badge_info["bonus_points"]
                        }
                    }
                )
            
            awarded_count += 1
            logger.info(
                f"✓ Badge awarded: {badge_info['name']} to user {user.id} "
                f"(+{badge_info['bonus_points']} points)"
            )
            
        except Exception as e:
            logger.error(f"Failed to award badge {badge_name} to user {user.id}: {str(e)}")
            continue
    
    return awarded_count


async def get_user_badges(db, user_id: int) -> List[Dict[str, Any]]:
    """
    Get all badges for a user with details
    
    Args:
        db: Database connection
        user_id: User ID
        
    Returns:
        List of badge details
    """
    try:
        badges = await db.badge.find_many(
            where={"user_id": user_id},
            order={"earned_at": "desc"}
        )
        
        badge_details = []
        for badge in badges:
            badge_info = BADGES.get(badge.badge_name, {})
            badge_details.append({
                "id": badge.id,
                "name": badge_info.get("name", badge.badge_name),
                "description": badge_info.get("description", ""),
                "icon": badge_info.get("icon", "🏅"),
                "earned_at": badge.earned_at.isoformat() if badge.earned_at else None,
                "bonus_points": badge_info.get("bonus_points", 0)
            })
        
        return badge_details
        
    except Exception as e:
        logger.error(f"Failed to get badges for user {user_id}: {str(e)}")
        return []


async def get_badge_progress(db, user_id: int) -> Dict[str, Any]:
    """
    Get user's progress toward earning badges
    
    Args:
        db: Database connection
        user_id: User ID
        
    Returns:
        Badge progress information
    """
    try:
        # Get user's existing badges
        existing_badges = await db.badge.find_many(
            where={"user_id": user_id}
        )
        existing_badge_names = {badge.badge_name for badge in existing_badges}
        
        # Count achievements
        rewards = await db.reward.find_many(
            where={
                "user_id": user_id,
                "status": "completed"
            }
        )
        
        wins = sum(1 for r in rewards if r.reason == "winning_vote")
        top_args = sum(1 for r in rewards if r.reason == "top_argument")
        participation = sum(1 for r in rewards if r.reason in ["winning_vote", "participation"])
        
        votes = await db.uservote.count(
            where={"user_id": user_id}
        )
        
        user = await db.user.find_unique(
            where={"id": user_id}
        )
        
        # Build progress report
        progress = {
            "earned": len(existing_badges),
            "total": len(BADGES),
            "progress_details": []
        }
        
        # Check each badge
        badge_checks = [
            ("first_win", wins >= 1, f"{wins}/1 wins"),
            ("five_wins", wins >= 5, f"{wins}/5 wins"),
            ("ten_wins", wins >= 10, f"{wins}/10 wins"),
            ("top_argument", top_args >= 1, f"{top_args}/1 top arguments"),
            ("top_argument_3x", top_args >= 3, f"{top_args}/3 top arguments"),
            ("active_participant", participation >= 20, f"{participation}/20 participations"),
            ("dedicated_voter", votes >= 50, f"{votes}/50 votes"),
            ("wallet_connected", bool(user and user.neo_wallet_address), "Wallet connected" if user and user.neo_wallet_address else "Not connected"),
        ]
        
        for badge_name, earned, progress_text in badge_checks:
            badge_info = BADGES.get(badge_name, {})
            progress["progress_details"].append({
                "badge_name": badge_name,
                "name": badge_info.get("name", badge_name),
                "description": badge_info.get("description", ""),
                "icon": badge_info.get("icon", "🏅"),
                "earned": badge_name in existing_badge_names,
                "progress": progress_text,
                "bonus_points": badge_info.get("bonus_points", 0)
            })
        
        return progress
        
    except Exception as e:
        logger.error(f"Failed to get badge progress for user {user_id}: {str(e)}")
        return {
            "earned": 0,
            "total": len(BADGES),
            "progress_details": [],
            "error": str(e)
        }
