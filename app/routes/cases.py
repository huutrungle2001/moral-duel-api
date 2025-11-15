from fastapi import APIRouter, HTTPException, status, Depends, Query
from prisma import Prisma
from typing import Optional
import json
import logging
import math

from app.utils.database import get_db
from app.utils.auth import get_current_user, get_current_user_optional
from app.services.case_service import CaseService
from app.services.ai_service import ai_service
from app.models.case_models import (
    CreateCaseRequest,
    VoteRequest,
    SubmitArgumentRequest,
    CaseListResponse,
    CaseListItem,
    CaseDetailResponse,
    ArgumentResponse,
    VoteResponse,
    UserBasicInfo,
    CaseStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=CaseListResponse)
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by status: pending_moderation, active, closed"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """List all cases with filters"""
    try:
        user_id = current_user.id if current_user else None
        
        cases, total = await CaseService.list_cases(
            db=db,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            user_id=user_id
        )
        
        # Transform cases to response format
        case_items = []
        for case in cases:
            # Find user's vote if authenticated
            user_voted_side = None
            if current_user:
                for vote in case.user_votes:
                    if vote.user_id == current_user.id:
                        user_voted_side = vote.side
                        break
            
            creator_info = None
            if case.creator:
                creator_info = UserBasicInfo(
                    id=case.creator.id,
                    name=case.creator.name,
                    total_points=case.creator.total_points
                )
            
            case_items.append(CaseListItem(
                id=case.id,
                title=case.title,
                context=case.context,
                status=case.status,
                yes_votes=case.yes_votes,
                no_votes=case.no_votes,
                total_participants=case.total_participants,
                is_ai_generated=case.is_ai_generated,
                created_at=case.created_at,
                closes_at=case.closes_at,
                closed_at=case.closed_at,
                creator=creator_info,
                user_voted_side=user_voted_side
            ))
        
        total_pages = math.ceil(total / page_size)
        
        return CaseListResponse(
            cases=case_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list cases"
        )


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: int,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Get case details"""
    try:
        user_id = current_user.id if current_user else None
        case = await CaseService.get_case_by_id(db=db, case_id=case_id, user_id=user_id)
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        # Get user's liked arguments
        liked_argument_ids = []
        if current_user:
            liked_argument_ids = await CaseService.get_user_liked_arguments(
                db=db, case_id=case_id, user_id=current_user.id
            )
        
        # Transform arguments to response format
        argument_responses = []
        for arg in case.arguments:
            is_liked = arg.id in liked_argument_ids
            
            user_info = UserBasicInfo(
                id=arg.user.id,
                name=arg.user.name,
                total_points=arg.user.total_points
            )
            
            argument_responses.append(ArgumentResponse(
                id=arg.id,
                case_id=arg.case_id,
                user=user_info,
                content=arg.content,
                side=arg.side,
                votes=arg.votes,
                is_top_3=arg.is_top_3,
                created_at=arg.created_at,
                is_liked_by_user=is_liked
            ))
        
        # Get user's vote
        user_vote_dict = None
        if current_user and case.user_votes:
            for vote in case.user_votes:
                if vote.user_id == current_user.id:
                    liked_args = json.loads(vote.liked_arguments) if vote.liked_arguments else []
                    user_vote_dict = {
                        "side": vote.side,
                        "voted_at": vote.voted_at.isoformat(),
                        "liked_arguments": liked_args,
                        "has_submitted_arg": vote.has_submitted_arg
                    }
                    break
        
        creator_info = None
        if case.creator:
            creator_info = UserBasicInfo(
                id=case.creator.id,
                name=case.creator.name,
                total_points=case.creator.total_points
            )
        
        # Hide verdict if case is not closed
        ai_verdict = case.ai_verdict if case.status == CaseStatus.CLOSED else None
        ai_verdict_reasoning = case.ai_verdict_reasoning if case.status == CaseStatus.CLOSED else None
        ai_confidence = case.ai_confidence if case.status == CaseStatus.CLOSED else None
        
        return CaseDetailResponse(
            id=case.id,
            title=case.title,
            context=case.context,
            status=case.status,
            ai_verdict=ai_verdict,
            ai_verdict_reasoning=ai_verdict_reasoning,
            ai_confidence=ai_confidence,
            yes_votes=case.yes_votes,
            no_votes=case.no_votes,
            total_participants=case.total_participants,
            is_ai_generated=case.is_ai_generated,
            created_at=case.created_at,
            closes_at=case.closes_at,
            closed_at=case.closed_at,
            creator=creator_info,
            arguments=argument_responses,
            user_vote=user_vote_dict,
            blockchain_tx_hash=case.blockchain_tx_hash,
            verdict_hash=case.verdict_hash
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting case {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get case"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CreateCaseRequest,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create user-submitted case with AI moderation"""
    try:
        # Run AI moderation check
        logger.info(f"Moderating case from user {current_user.id}")
        approved, reason = await ai_service.moderate_case(data.title, data.context)
        
        if not approved:
            logger.warning(f"Case rejected: {reason}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content not approved: {reason or 'Inappropriate content detected'}"
            )
        
        case = await CaseService.create_case(
            db=db,
            title=data.title,
            context=data.context,
            user_id=current_user.id,
            is_ai_generated=False
        )
        
        logger.info(f"✓ User {current_user.id} created case {case.id}")
        
        return {
            "message": "Case created successfully",
            "case_id": case.id,
            "status": case.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create case"
        )


@router.get("/{case_id}/blockchain")
async def get_case_blockchain(case_id: int):
    """Get blockchain verification data"""
    return {"message": f"Case {case_id} blockchain endpoint - implementation pending"}


@router.get("/{case_id}/ai-verdict")
async def get_ai_verdict(
    case_id: int,
    db: Prisma = Depends(get_db)
):
    """Get AI verdict and reasoning (closed cases only)"""
    try:
        # Get case
        case = await db.case.find_unique(
            where={"id": case_id}
        )
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        
        # Only allow verdict for closed cases
        if case.status != "closed":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI verdict only available for closed cases"
            )
        
        # Return verdict data
        return {
            "case_id": case.id,
            "verdict": case.ai_verdict,
            "reasoning": case.ai_verdict_reasoning,
            "confidence": case.ai_confidence,
            "verdict_hash": case.verdict_hash,
            "blockchain_tx_hash": case.blockchain_tx_hash,
            "yes_votes": case.yes_votes,
            "no_votes": case.no_votes,
            "closed_at": case.closed_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI verdict {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get AI verdict"
        )


@router.post("/{case_id}/vote", response_model=VoteResponse)
async def vote_on_case(
    case_id: int,
    data: VoteRequest,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Vote YES/NO on a case"""
    try:
        updated_case, user_vote = await CaseService.vote_on_case(
            db=db,
            case_id=case_id,
            user_id=current_user.id,
            side=data.side
        )
        
        logger.info(f"User {current_user.id} voted {data.side.value} on case {case_id}")
        
        return VoteResponse(
            message="Vote recorded successfully",
            case_id=updated_case.id,
            side=user_vote.side,
            yes_votes=updated_case.yes_votes,
            no_votes=updated_case.no_votes,
            total_participants=updated_case.total_participants
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error voting on case {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record vote"
        )


@router.post("/{case_id}/arguments", status_code=status.HTTP_201_CREATED)
async def submit_argument(
    case_id: int,
    data: SubmitArgumentRequest,
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit argument after voting"""
    try:
        argument = await CaseService.submit_argument(
            db=db,
            case_id=case_id,
            user_id=current_user.id,
            content=data.content,
            side=data.side
        )
        
        logger.info(f"User {current_user.id} submitted argument for case {case_id}")
        
        return {
            "message": "Argument submitted successfully",
            "argument_id": argument.id,
            "case_id": argument.case_id,
            "side": argument.side
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error submitting argument for case {case_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit argument"
        )
