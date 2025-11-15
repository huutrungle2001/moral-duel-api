from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from prisma import Prisma
from typing import Optional, List
from datetime import datetime
import logging

from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.services.reward_service import reward_service
from app.services.blockchain_service import blockchain_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ClaimRewardsRequest(BaseModel):
    reward_ids: List[int]
    neo_wallet_address: Optional[str] = None


@router.get("")
async def get_profile(
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user profile with complete information"""
    try:
        # Get user with related data
        user = await db.user.find_unique(
            where={"id": current_user.id},
            include={
                "user_votes": {
                    "include": {
                        "case": True
                    }
                },
                "arguments": {
                    "include": {
                        "case": True
                    }
                },
                "cases": True
            }
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Calculate voting stats
        closed_votes = [v for v in user.user_votes if v.case.status == "closed"]
        correct_votes = sum(1 for v in closed_votes if v.side == v.case.ai_verdict)
        voting_accuracy = (correct_votes / len(closed_votes) * 100) if closed_votes else 0
        
        # Get recent activity
        recent_votes = sorted(user.user_votes, key=lambda x: x.voted_at, reverse=True)[:5]
        recent_arguments = sorted(user.arguments, key=lambda x: x.created_at, reverse=True)[:5]
        
        # Count top arguments
        top_arguments_count = sum(1 for arg in user.arguments if arg.is_top_3)
        
        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "neo_wallet_address": user.neo_wallet_address,
                "total_points": user.total_points,
                "created_at": user.created_at
            },
            "statistics": {
                "total_votes": len(user.user_votes),
                "total_arguments": len(user.arguments),
                "total_cases_created": len(user.cases),
                "voting_accuracy": round(voting_accuracy, 2),
                "correct_votes": correct_votes,
                "top_arguments": top_arguments_count
            },
            "recent_activity": {
                "recent_votes": [
                    {
                        "case_id": vote.case.id,
                        "case_title": vote.case.title,
                        "side": vote.side,
                        "voted_at": vote.voted_at,
                        "case_status": vote.case.status,
                        "was_correct": vote.side == vote.case.ai_verdict if vote.case.ai_verdict else None
                    }
                    for vote in recent_votes
                ],
                "recent_arguments": [
                    {
                        "id": arg.id,
                        "case_id": arg.case.id,
                        "case_title": arg.case.title,
                        "content": arg.content,
                        "votes": arg.votes,
                        "is_top_3": arg.is_top_3,
                        "created_at": arg.created_at
                    }
                    for arg in recent_arguments
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@router.get("/stats")
async def get_profile_stats(
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed user statistics"""
    try:
        # Get all user votes with case info
        votes = await db.uservote.find_many(
            where={"user_id": current_user.id},
            include={
                "case": True
            }
        )
        
        # Calculate statistics
        yes_votes = sum(1 for v in votes if v.side == "YES")
        no_votes = sum(1 for v in votes if v.side == "NO")
        
        # Votes on closed cases
        closed_votes = [v for v in votes if v.case.status == "closed"]
        correct_votes = sum(1 for v in closed_votes if v.side == v.case.ai_verdict)
        
        # Get arguments
        arguments = await db.argument.find_many(
            where={"user_id": current_user.id}
        )
        
        total_argument_likes = sum(arg.votes for arg in arguments)
        top_arguments = sum(1 for arg in arguments if arg.is_top_3)
        
        # Get created cases
        created_cases = await db.case.find_many(
            where={"created_by_id": current_user.id}
        )
        
        active_cases = sum(1 for c in created_cases if c.status == "active")
        closed_cases = sum(1 for c in created_cases if c.status == "closed")
        
        return {
            "voting": {
                "total_votes": len(votes),
                "yes_votes": yes_votes,
                "no_votes": no_votes,
                "votes_on_closed_cases": len(closed_votes),
                "correct_votes": correct_votes,
                "voting_accuracy": round((correct_votes / len(closed_votes) * 100) if closed_votes else 0, 2)
            },
            "arguments": {
                "total_arguments": len(arguments),
                "total_likes_received": total_argument_likes,
                "top_arguments": top_arguments,
                "average_likes": round(total_argument_likes / len(arguments), 2) if arguments else 0
            },
            "cases": {
                "total_created": len(created_cases),
                "active": active_cases,
                "closed": closed_cases
            },
            "overall": {
                "total_points": current_user.total_points,
                "account_age_days": (current_user.updated_at - current_user.created_at).days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting profile stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile statistics"
        )


@router.get("/rewards")
async def get_user_rewards(
    status_filter: Optional[str] = None,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get user's reward history
    
    Query params:
        status_filter: Filter by status (pending, processing, completed, failed)
        
    Returns list of rewards with case details
    """
    try:
        rewards = await reward_service.get_user_rewards(
            db,
            current_user.id,
            status=status_filter
        )
        
        # Get reward statistics
        stats = await reward_service.get_reward_statistics(db, current_user.id)
        
        return {
            "rewards": [
                {
                    "id": r.id,
                    "case_id": r.case_id,
                    "case_title": r.case.title if r.case else "Unknown",
                    "amount": r.amount,
                    "type": r.type,
                    "status": r.status,
                    "created_at": r.created_at,
                    "claimed_at": r.claimed_at,
                    "completed_at": r.completed_at,
                    "blockchain_tx_hash": r.blockchain_tx_hash
                }
                for r in rewards
            ],
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user rewards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rewards"
        )


@router.post("/rewards/claim")
async def claim_rewards(
    request: ClaimRewardsRequest,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Claim pending rewards
    
    Request body:
        reward_ids: List of reward IDs to claim
        neo_wallet_address: Neo wallet address (optional if already set)
        
    Returns transaction details and updated reward status
    """
    try:
        # Check if user has Neo wallet
        user = await db.user.find_unique(where={"id": current_user.id})
        
        wallet_address = request.neo_wallet_address or user.neo_wallet_address
        
        if not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Neo wallet address required. Please connect your wallet first."
            )
        
        # Validate rewards belong to user and are claimable
        rewards = await db.reward.find_many(
            where={
                "id": {"in": request.reward_ids},
                "user_id": current_user.id,
                "status": "pending"
            }
        )
        
        if not rewards:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No claimable rewards found with provided IDs"
            )
        
        if len(rewards) != len(request.reward_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some rewards are not claimable (already claimed or don't belong to you)"
            )
        
        # Calculate total amount
        total_amount = sum(r.amount for r in rewards)
        
        logger.info(
            f"User {current_user.id} claiming {len(rewards)} rewards, "
            f"total amount: {total_amount:.2f}"
        )
        
        # TODO: Create blockchain transaction to transfer tokens
        # For now, simulate the transaction
        blockchain_tx = {
            "success": True,
            "mock": True,
            "tx_hash": f"reward_claim_{current_user.id}_{datetime.now().timestamp()}",
            "wallet_address": wallet_address,
            "amount": total_amount,
            "reward_count": len(rewards)
        }
        
        # Update reward records
        updated_rewards = []
        for reward in rewards:
            updated = await reward_service.mark_reward_claimed(
                db,
                reward.id,
                blockchain_tx["tx_hash"]
            )
            updated_rewards.append(updated)
        
        logger.info(f"✓ Rewards claimed: {len(updated_rewards)} rewards, TX={blockchain_tx['tx_hash'][:16]}...")
        
        return {
            "success": True,
            "message": f"Successfully claimed {len(rewards)} rewards",
            "total_amount": total_amount,
            "rewards_claimed": len(rewards),
            "transaction": blockchain_tx,
            "note": "Blockchain transaction processing. Tokens will be transferred shortly."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming rewards: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to claim rewards: {str(e)}"
        )


@router.get("/rewards/{reward_id}/status")
async def get_reward_status(
    reward_id: int,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get status of a specific reward
    
    Returns reward details including blockchain transaction status
    """
    try:
        reward = await db.reward.find_unique(
            where={"id": reward_id},
            include={"case": True}
        )
        
        if not reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found"
            )
        
        if reward.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this reward"
            )
        
        result = {
            "id": reward.id,
            "case_id": reward.case_id,
            "case_title": reward.case.title if reward.case else "Unknown",
            "amount": reward.amount,
            "type": reward.type,
            "status": reward.status,
            "created_at": reward.created_at,
            "claimed_at": reward.claimed_at,
            "completed_at": reward.completed_at,
            "blockchain_tx_hash": reward.blockchain_tx_hash
        }
        
        # If reward has blockchain transaction, get its status
        if reward.blockchain_tx_hash and blockchain_service.enabled:
            try:
                tx_status = await blockchain_service.get_transaction(reward.blockchain_tx_hash)
                result["transaction_status"] = tx_status
            except Exception as e:
                logger.error(f"Failed to get transaction status: {str(e)}")
                result["transaction_status"] = {
                    "status": "unknown",
                    "error": str(e)
                }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reward status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reward status"
        )
