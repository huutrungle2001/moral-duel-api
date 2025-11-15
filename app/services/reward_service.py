"""
Reward Calculation and Distribution Service

Handles:
- Reward pool calculation for closed cases
- Distribution logic (40% winners, 30% top args, 20% participants, 10% creator)
- Reward record creation in database
- Integration with blockchain for token distribution
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from prisma import Prisma
from prisma.models import Case, User, UserVote, Argument, Reward

logger = logging.getLogger(__name__)


class RewardService:
    """Service for calculating and distributing rewards"""
    
    # Reward distribution percentages
    WINNING_VOTERS_PERCENTAGE = 0.40  # 40%
    TOP_ARGUMENTS_PERCENTAGE = 0.30   # 30%
    PARTICIPANTS_PERCENTAGE = 0.20     # 20%
    CREATOR_PERCENTAGE = 0.10         # 10%
    
    # Top 3 argument weights (must sum to 1.0)
    TOP_1_WEIGHT = 0.50  # 50% of top arguments pool
    TOP_2_WEIGHT = 0.30  # 30% of top arguments pool
    TOP_3_WEIGHT = 0.20  # 20% of top arguments pool
    
    # Minimum participants for creator reward
    MIN_PARTICIPANTS_FOR_CREATOR = 100
    
    @staticmethod
    async def calculate_rewards(db: Prisma, case: Case) -> Dict[str, any]:
        """
        Calculate reward distribution for a closed case
        
        Args:
            db: Database instance
            case: Closed case with verdict revealed
            
        Returns:
            Dict containing reward calculations and eligible users
        """
        try:
            if case.status != "closed":
                raise ValueError("Case must be closed to calculate rewards")
            
            if not case.ai_verdict:
                raise ValueError("Case must have a verdict to calculate rewards")
            
            # Get reward pool
            reward_pool = float(case.reward_pool) if case.reward_pool else 0.0
            
            if reward_pool <= 0:
                logger.info(f"Case {case.id} has no reward pool, skipping reward calculation")
                return {
                    "case_id": case.id,
                    "reward_pool": 0.0,
                    "total_participants": 0,
                    "distributions": []
                }
            
            logger.info(f"Calculating rewards for case {case.id}: Pool={reward_pool}")
            
            # Get all votes
            votes = await db.uservote.find_many(
                where={"case_id": case.id},
                include={"user": True}
            )
            
            # Get all arguments
            arguments = await db.argument.find_many(
                where={"case_id": case.id},
                include={"user": True},
                order={"votes": "desc"}
            )
            
            total_participants = case.total_participants
            
            # Calculate distributions
            distributions = []
            
            # 1. Winning side voters (40%)
            winning_voters_pool = reward_pool * RewardService.WINNING_VOTERS_PERCENTAGE
            winning_voters = [v for v in votes if v.side == case.ai_verdict]
            
            if winning_voters:
                reward_per_winner = winning_voters_pool / len(winning_voters)
                for vote in winning_voters:
                    distributions.append({
                        "user_id": vote.user_id,
                        "user_name": vote.user.name if vote.user else "Unknown",
                        "amount": reward_per_winner,
                        "type": "winning_voter",
                        "description": f"Voted {case.ai_verdict} (correct)"
                    })
                logger.info(f"Winning voters: {len(winning_voters)} users, {reward_per_winner:.2f} each")
            else:
                logger.warning(f"Case {case.id}: No winning voters found")
            
            # 2. Top 3 arguments (30%)
            top_args_pool = reward_pool * RewardService.TOP_ARGUMENTS_PERCENTAGE
            top_3_args = [arg for arg in arguments if arg.is_top_3][:3]
            
            if top_3_args:
                weights = [RewardService.TOP_1_WEIGHT, RewardService.TOP_2_WEIGHT, RewardService.TOP_3_WEIGHT]
                for i, arg in enumerate(top_3_args):
                    weight = weights[i] if i < len(weights) else 0
                    amount = top_args_pool * weight
                    distributions.append({
                        "user_id": arg.user_id,
                        "user_name": arg.user.name if arg.user else "Unknown",
                        "amount": amount,
                        "type": "top_argument",
                        "description": f"Top {i+1} argument ({arg.votes} votes)",
                        "rank": i + 1
                    })
                logger.info(f"Top arguments: {len(top_3_args)} arguments rewarded")
            else:
                logger.warning(f"Case {case.id}: No top arguments marked")
            
            # 3. All participants (20%)
            participants_pool = reward_pool * RewardService.PARTICIPANTS_PERCENTAGE
            
            if total_participants > 0:
                reward_per_participant = participants_pool / total_participants
                
                # Get unique participants (voters + argument authors)
                participant_ids = set()
                for vote in votes:
                    participant_ids.add(vote.user_id)
                for arg in arguments:
                    participant_ids.add(arg.user_id)
                
                # Get user info for participants
                participants = await db.user.find_many(
                    where={"id": {"in": list(participant_ids)}}
                )
                
                for user in participants:
                    distributions.append({
                        "user_id": user.id,
                        "user_name": user.name,
                        "amount": reward_per_participant,
                        "type": "participant",
                        "description": "Participation reward"
                    })
                logger.info(f"Participants: {len(participants)} users, {reward_per_participant:.2f} each")
            
            # 4. Case creator (10% if ≥100 participants)
            if case.created_by_id and total_participants >= RewardService.MIN_PARTICIPANTS_FOR_CREATOR:
                creator_pool = reward_pool * RewardService.CREATOR_PERCENTAGE
                creator = await db.user.find_unique(where={"id": case.created_by_id})
                
                if creator:
                    distributions.append({
                        "user_id": creator.id,
                        "user_name": creator.name,
                        "amount": creator_pool,
                        "type": "creator",
                        "description": f"Created popular case ({total_participants} participants)"
                    })
                    logger.info(f"Creator reward: {creator.name}, {creator_pool:.2f}")
            else:
                if case.created_by_id:
                    logger.info(f"Creator reward skipped: only {total_participants} participants (need {RewardService.MIN_PARTICIPANTS_FOR_CREATOR})")
            
            return {
                "case_id": case.id,
                "case_title": case.title,
                "reward_pool": reward_pool,
                "total_participants": total_participants,
                "verdict": case.ai_verdict,
                "distributions": distributions,
                "summary": {
                    "winning_voters": len(winning_voters),
                    "top_arguments": len(top_3_args),
                    "participants": len(participant_ids) if total_participants > 0 else 0,
                    "creator_rewarded": case.created_by_id and total_participants >= RewardService.MIN_PARTICIPANTS_FOR_CREATOR
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating rewards for case {case.id}: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def create_reward_records(
        db: Prisma,
        case_id: int,
        distributions: List[Dict]
    ) -> List[Reward]:
        """
        Create reward records in database
        
        Args:
            db: Database instance
            case_id: Case ID
            distributions: List of reward distributions from calculate_rewards
            
        Returns:
            List of created reward records
        """
        try:
            rewards = []
            
            # Group distributions by user to avoid duplicates
            user_rewards = {}
            for dist in distributions:
                user_id = dist["user_id"]
                if user_id not in user_rewards:
                    user_rewards[user_id] = {
                        "user_id": user_id,
                        "case_id": case_id,
                        "total_amount": 0.0,
                        "types": []
                    }
                user_rewards[user_id]["total_amount"] += dist["amount"]
                user_rewards[user_id]["types"].append(dist["type"])
            
            # Create reward records
            for user_id, reward_data in user_rewards.items():
                reward = await db.reward.create(
                    data={
                        "user_id": user_id,
                        "case_id": case_id,
                        "amount": reward_data["total_amount"],
                        "type": ", ".join(set(reward_data["types"])),
                        "status": "pending",
                        "created_at": datetime.utcnow()
                    }
                )
                rewards.append(reward)
                logger.info(
                    f"Created reward: User {user_id}, "
                    f"Amount {reward_data['total_amount']:.2f}, "
                    f"Types {reward_data['types']}"
                )
            
            logger.info(f"Created {len(rewards)} reward records for case {case_id}")
            return rewards
            
        except Exception as e:
            logger.error(f"Error creating reward records: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_user_rewards(
        db: Prisma,
        user_id: int,
        status: Optional[str] = None
    ) -> List[Reward]:
        """
        Get rewards for a user
        
        Args:
            db: Database instance
            user_id: User ID
            status: Optional status filter (pending, processing, completed, failed)
            
        Returns:
            List of rewards
        """
        where_clause = {"user_id": user_id}
        if status:
            where_clause["status"] = status
        
        rewards = await db.reward.find_many(
            where=where_clause,
            include={"case": True},
            order={"created_at": "desc"}
        )
        
        return rewards
    
    @staticmethod
    async def mark_reward_claimed(
        db: Prisma,
        reward_id: int,
        blockchain_tx_hash: str
    ) -> Reward:
        """
        Mark reward as claimed with blockchain transaction
        
        Args:
            db: Database instance
            reward_id: Reward ID
            blockchain_tx_hash: Transaction hash from blockchain
            
        Returns:
            Updated reward record
        """
        reward = await db.reward.update(
            where={"id": reward_id},
            data={
                "status": "processing",
                "blockchain_tx_hash": blockchain_tx_hash,
                "claimed_at": datetime.utcnow()
            }
        )
        
        logger.info(f"Reward {reward_id} marked as claimed: TX {blockchain_tx_hash[:16]}...")
        return reward
    
    @staticmethod
    async def mark_reward_completed(
        db: Prisma,
        reward_id: int
    ) -> Reward:
        """
        Mark reward as completed (transaction confirmed)
        
        Args:
            db: Database instance
            reward_id: Reward ID
            
        Returns:
            Updated reward record
        """
        reward = await db.reward.update(
            where={"id": reward_id},
            data={
                "status": "completed",
                "completed_at": datetime.utcnow()
            }
        )
        
        # Update user's total points
        await db.user.update(
            where={"id": reward.user_id},
            data={
                "total_points": {
                    "increment": int(reward.amount)
                }
            }
        )
        
        logger.info(f"Reward {reward_id} completed, user points updated")
        return reward
    
    @staticmethod
    async def get_reward_statistics(db: Prisma, user_id: int) -> Dict:
        """
        Get reward statistics for a user
        
        Args:
            db: Database instance
            user_id: User ID
            
        Returns:
            Statistics dict
        """
        rewards = await db.reward.find_many(
            where={"user_id": user_id}
        )
        
        total_earned = sum(r.amount for r in rewards)
        pending = sum(r.amount for r in rewards if r.status == "pending")
        completed = sum(r.amount for r in rewards if r.status == "completed")
        
        return {
            "total_rewards": len(rewards),
            "total_earned": total_earned,
            "pending": pending,
            "completed": completed,
            "by_type": {
                "winning_voter": sum(r.amount for r in rewards if "winning_voter" in r.type),
                "top_argument": sum(r.amount for r in rewards if "top_argument" in r.type),
                "participant": sum(r.amount for r in rewards if "participant" in r.type),
                "creator": sum(r.amount for r in rewards if "creator" in r.type)
            }
        }


# Global service instance
reward_service = RewardService()
