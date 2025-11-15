from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from prisma import Prisma
from prisma.models import Case, Argument, UserVote, ArgumentVote, User
import json
import logging

from app.models.case_models import CaseStatus, VoteSide

logger = logging.getLogger(__name__)


class CaseService:
    """Service layer for case management business logic"""

    @staticmethod
    async def list_cases(
        db: Prisma,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        user_id: Optional[int] = None
    ) -> tuple[List[Case], int]:
        """
        List cases with filtering, pagination, and sorting
        Returns: (cases, total_count)
        """
        where_clause: Dict[str, Any] = {}
        
        if status:
            where_clause["status"] = status
        
        skip = (page - 1) * page_size
        
        # Build order by clause
        order_by = {sort_by: sort_order}
        
        # Get total count
        total = await db.case.count(where=where_clause)
        
        # Get paginated cases
        cases = await db.case.find_many(
            where=where_clause,
            include={
                "creator": True,
                "user_votes": True if user_id else False,
            },
            order=order_by,
            skip=skip,
            take=page_size,
        )
        
        return cases, total

    @staticmethod
    async def get_case_by_id(db: Prisma, case_id: int, user_id: Optional[int] = None) -> Optional[Case]:
        """Get case by ID with all related data"""
        case = await db.case.find_unique(
            where={"id": case_id},
            include={
                "creator": True,
                "arguments": {
                    "include": {
                        "user": True,
                        "argument_votes": True if user_id else False,
                    },
                    "order": {"votes": "desc"}
                },
                "user_votes": {
                    "where": {"user_id": user_id} if user_id else {}
                }
            }
        )
        return case

    @staticmethod
    async def create_case(
        db: Prisma,
        title: str,
        context: str,
        user_id: int,
        is_ai_generated: bool = False
    ) -> Case:
        """Create a new case"""
        # User-submitted cases go into pending moderation
        # AI-generated cases go directly to active
        status = CaseStatus.ACTIVE if is_ai_generated else CaseStatus.PENDING_MODERATION
        
        # Calculate closes_at (24 hours from now for active cases)
        closes_at = datetime.utcnow() + timedelta(hours=24) if status == CaseStatus.ACTIVE else None
        
        case = await db.case.create(
            data={
                "title": title,
                "context": context,
                "status": status,
                "created_by_id": user_id,
                "is_ai_generated": is_ai_generated,
                "closes_at": closes_at,
            }
        )
        
        logger.info(f"Case created: {case.id} by user {user_id}")
        return case

    @staticmethod
    async def vote_on_case(
        db: Prisma,
        case_id: int,
        user_id: int,
        side: VoteSide
    ) -> tuple[Case, UserVote]:
        """
        Vote on a case
        Returns: (updated_case, user_vote)
        """
        # Check if case exists and is active
        case = await db.case.find_unique(where={"id": case_id})
        if not case:
            raise ValueError("Case not found")
        
        if case.status != CaseStatus.ACTIVE:
            raise ValueError("Case is not active for voting")
        
        # Check if case is still open
        if case.closes_at and case.closes_at < datetime.utcnow():
            raise ValueError("Case voting period has closed")
        
        # Check if user already voted
        existing_vote = await db.uservote.find_unique(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}}
        )
        
        if existing_vote:
            raise ValueError("User has already voted on this case")
        
        # Create vote
        user_vote = await db.uservote.create(
            data={
                "user_id": user_id,
                "case_id": case_id,
                "side": side.value,
            }
        )
        
        # Update case vote counts
        update_data = {
            "total_participants": case.total_participants + 1
        }
        
        if side == VoteSide.YES:
            update_data["yes_votes"] = case.yes_votes + 1
        else:
            update_data["no_votes"] = case.no_votes + 1
        
        updated_case = await db.case.update(
            where={"id": case_id},
            data=update_data
        )
        
        logger.info(f"User {user_id} voted {side.value} on case {case_id}")
        return updated_case, user_vote

    @staticmethod
    async def submit_argument(
        db: Prisma,
        case_id: int,
        user_id: int,
        content: str,
        side: VoteSide
    ) -> Argument:
        """Submit an argument for a case"""
        # Check if case exists and is active
        case = await db.case.find_unique(where={"id": case_id})
        if not case:
            raise ValueError("Case not found")
        
        if case.status != CaseStatus.ACTIVE:
            raise ValueError("Case is not active")
        
        # Check if user has voted
        user_vote = await db.uservote.find_unique(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}}
        )
        
        if not user_vote:
            raise ValueError("User must vote before submitting arguments")
        
        # Check if user already submitted an argument
        if user_vote.has_submitted_arg:
            raise ValueError("User has already submitted an argument for this case")
        
        # Check if user has liked 3 arguments
        liked_arguments = json.loads(user_vote.liked_arguments) if user_vote.liked_arguments else []
        if len(liked_arguments) < 3:
            raise ValueError("User must like 3 arguments before submitting their own")
        
        # Create argument
        argument = await db.argument.create(
            data={
                "case_id": case_id,
                "user_id": user_id,
                "content": content,
                "side": side.value,
            }
        )
        
        # Mark that user has submitted argument
        await db.uservote.update(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}},
            data={"has_submitted_arg": True}
        )
        
        logger.info(f"User {user_id} submitted argument for case {case_id}")
        return argument

    @staticmethod
    async def vote_on_argument(
        db: Prisma,
        argument_id: int,
        user_id: int,
        case_id: int
    ) -> tuple[Argument, bool]:
        """
        Vote (like) an argument
        Returns: (updated_argument, is_new_vote)
        """
        # Check if argument exists
        argument = await db.argument.find_unique(where={"id": argument_id})
        if not argument:
            raise ValueError("Argument not found")
        
        if argument.case_id != case_id:
            raise ValueError("Argument does not belong to this case")
        
        # Check if case is active
        case = await db.case.find_unique(where={"id": case_id})
        if not case or case.status != CaseStatus.ACTIVE:
            raise ValueError("Case is not active")
        
        # Check if user has voted on the case
        user_vote = await db.uservote.find_unique(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}}
        )
        
        if not user_vote:
            raise ValueError("User must vote on case before liking arguments")
        
        # Check if user already liked this argument
        existing_vote = await db.argumentvote.find_unique(
            where={"user_id_argument_id": {"user_id": user_id, "argument_id": argument_id}}
        )
        
        if existing_vote:
            raise ValueError("User has already liked this argument")
        
        # Check if user has reached max likes for this case (3)
        liked_arguments = json.loads(user_vote.liked_arguments) if user_vote.liked_arguments else []
        if len(liked_arguments) >= 3:
            raise ValueError("User can only like 3 arguments per case")
        
        # Create argument vote
        await db.argumentvote.create(
            data={
                "user_id": user_id,
                "argument_id": argument_id,
            }
        )
        
        # Update argument vote count
        updated_argument = await db.argument.update(
            where={"id": argument_id},
            data={"votes": argument.votes + 1}
        )
        
        # Update user's liked arguments
        liked_arguments.append(argument_id)
        await db.uservote.update(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}},
            data={"liked_arguments": json.dumps(liked_arguments)}
        )
        
        logger.info(f"User {user_id} liked argument {argument_id}")
        return updated_argument, True

    @staticmethod
    async def unvote_argument(
        db: Prisma,
        argument_id: int,
        user_id: int,
        case_id: int
    ) -> tuple[Argument, bool]:
        """
        Remove vote (unlike) from an argument
        Returns: (updated_argument, was_removed)
        """
        # Check if argument exists
        argument = await db.argument.find_unique(where={"id": argument_id})
        if not argument:
            raise ValueError("Argument not found")
        
        if argument.case_id != case_id:
            raise ValueError("Argument does not belong to this case")
        
        # Check if user voted on this argument
        existing_vote = await db.argumentvote.find_unique(
            where={"user_id_argument_id": {"user_id": user_id, "argument_id": argument_id}}
        )
        
        if not existing_vote:
            raise ValueError("User has not liked this argument")
        
        # Delete argument vote
        await db.argumentvote.delete(
            where={"user_id_argument_id": {"user_id": user_id, "argument_id": argument_id}}
        )
        
        # Update argument vote count
        updated_argument = await db.argument.update(
            where={"id": argument_id},
            data={"votes": max(0, argument.votes - 1)}
        )
        
        # Update user's liked arguments
        user_vote = await db.uservote.find_unique(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}}
        )
        
        if user_vote and user_vote.liked_arguments:
            liked_arguments = json.loads(user_vote.liked_arguments)
            if argument_id in liked_arguments:
                liked_arguments.remove(argument_id)
                await db.uservote.update(
                    where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}},
                    data={"liked_arguments": json.dumps(liked_arguments)}
                )
        
        logger.info(f"User {user_id} unliked argument {argument_id}")
        return updated_argument, True

    @staticmethod
    async def get_user_vote_for_case(db: Prisma, case_id: int, user_id: int) -> Optional[UserVote]:
        """Get user's vote for a specific case"""
        return await db.uservote.find_unique(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}}
        )

    @staticmethod
    async def get_user_liked_arguments(db: Prisma, case_id: int, user_id: int) -> List[int]:
        """Get list of argument IDs user has liked for a case"""
        user_vote = await db.uservote.find_unique(
            where={"user_id_case_id": {"user_id": user_id, "case_id": case_id}}
        )
        
        if user_vote and user_vote.liked_arguments:
            return json.loads(user_vote.liked_arguments)
        return []
