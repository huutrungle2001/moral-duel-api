from fastapi import APIRouter, HTTPException, status, Depends, Query
from prisma import Prisma
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def get_leaderboard(
    timeframe: str = Query("all_time", description="Timeframe: all_time, monthly, weekly"),
    limit: int = Query(100, ge=1, le=500, description="Number of users to return"),
    db: Prisma = Depends(get_db)
):
    """
    Get top users by points
    
    Timeframes:
    - all_time: All-time leaderboard
    - monthly: Last 30 days
    - weekly: Last 7 days
    """
    try:
        # Calculate date filter based on timeframe
        date_filter = None
        if timeframe == "monthly":
            date_filter = datetime.utcnow() - timedelta(days=30)
        elif timeframe == "weekly":
            date_filter = datetime.utcnow() - timedelta(days=7)
        elif timeframe != "all_time":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timeframe. Use: all_time, monthly, or weekly"
            )
        
        # Get top users by total points
        users = await db.user.find_many(
            take=limit,
            order={
                "total_points": "desc"
            }
        )
        
        # For time-filtered leaderboards, we need to recalculate points
        if date_filter:
            user_scores = []
            
            for user in users:
                # Get votes in timeframe
                votes = await db.uservote.find_many(
                    where={
                        "user_id": user.id,
                        "voted_at": {"gte": date_filter}
                    },
                    include={"case": True}
                )
                
                # Get arguments in timeframe
                arguments = await db.argument.find_many(
                    where={
                        "user_id": user.id,
                        "created_at": {"gte": date_filter}
                    }
                )
                
                # Calculate points for this timeframe
                # Simple scoring: 10 points per vote, 5 per argument, 20 per top argument
                points = len(votes) * 10
                points += len(arguments) * 5
                points += sum(20 for arg in arguments if arg.is_top_3)
                
                # Calculate voting accuracy
                closed_votes = [v for v in votes if v.case.status == "closed" and v.case.ai_verdict]
                correct_votes = sum(1 for v in closed_votes if v.side == v.case.ai_verdict)
                accuracy = (correct_votes / len(closed_votes) * 100) if closed_votes else 0
                
                user_scores.append({
                    "rank": 0,  # Will be set after sorting
                    "user_id": user.id,
                    "name": user.name,
                    "points": points,
                    "stats": {
                        "total_votes": len(votes),
                        "total_arguments": len(arguments),
                        "top_arguments": sum(1 for arg in arguments if arg.is_top_3),
                        "voting_accuracy": round(accuracy, 2)
                    }
                })
            
            # Sort by points and assign ranks
            user_scores.sort(key=lambda x: x["points"], reverse=True)
            for i, score in enumerate(user_scores, 1):
                score["rank"] = i
            
            return {
                "timeframe": timeframe,
                "total_users": len(user_scores),
                "leaderboard": user_scores[:limit]
            }
        
        else:
            # All-time leaderboard using total_points
            leaderboard = []
            
            for i, user in enumerate(users, 1):
                # Get voting accuracy
                votes = await db.uservote.find_many(
                    where={"user_id": user.id},
                    include={"case": True}
                )
                
                closed_votes = [v for v in votes if v.case.status == "closed" and v.case.ai_verdict]
                correct_votes = sum(1 for v in closed_votes if v.side == v.case.ai_verdict)
                accuracy = (correct_votes / len(closed_votes) * 100) if closed_votes else 0
                
                # Get arguments count and top arguments
                arguments = await db.argument.find_many(
                    where={"user_id": user.id}
                )
                top_args = sum(1 for arg in arguments if arg.is_top_3)
                
                # Get cases created count
                cases_count = await db.case.count(
                    where={"created_by_id": user.id}
                )
                
                leaderboard.append({
                    "rank": i,
                    "user_id": user.id,
                    "name": user.name,
                    "points": user.total_points,
                    "stats": {
                        "total_votes": len(votes),
                        "total_arguments": len(arguments),
                        "top_arguments": top_args,
                        "cases_created": cases_count,
                        "voting_accuracy": round(accuracy, 2)
                    }
                })
            
            return {
                "timeframe": timeframe,
                "total_users": len(leaderboard),
                "leaderboard": leaderboard
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get leaderboard"
        )
