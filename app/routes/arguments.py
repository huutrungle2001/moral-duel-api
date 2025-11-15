from fastapi import APIRouter, HTTPException, status, Depends, Query
from prisma import Prisma
import logging

from app.utils.database import get_db
from app.utils.auth import get_current_user
from app.services.case_service import CaseService
from app.models.case_models import ArgumentVoteResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{argument_id}/vote", response_model=ArgumentVoteResponse)
async def vote_argument(
    argument_id: int,
    case_id: int = Query(..., description="Case ID to which argument belongs"),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Like an argument (max 3 per case)"""
    try:
        updated_argument, is_new = await CaseService.vote_on_argument(
            db=db,
            argument_id=argument_id,
            user_id=current_user.id,
            case_id=case_id
        )
        
        logger.info(f"User {current_user.id} liked argument {argument_id}")
        
        return ArgumentVoteResponse(
            message="Argument liked successfully",
            argument_id=updated_argument.id,
            votes=updated_argument.votes,
            is_liked=True
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error voting on argument {argument_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to vote on argument"
        )


@router.delete("/{argument_id}/vote", response_model=ArgumentVoteResponse)
async def unvote_argument(
    argument_id: int,
    case_id: int = Query(..., description="Case ID to which argument belongs"),
    db: Prisma = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Unlike an argument"""
    try:
        updated_argument, was_removed = await CaseService.unvote_argument(
            db=db,
            argument_id=argument_id,
            user_id=current_user.id,
            case_id=case_id
        )
        
        logger.info(f"User {current_user.id} unliked argument {argument_id}")
        
        return ArgumentVoteResponse(
            message="Argument unliked successfully",
            argument_id=updated_argument.id,
            votes=updated_argument.votes,
            is_liked=False
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error unvoting argument {argument_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unvote argument"
        )
