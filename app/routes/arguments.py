from fastapi import APIRouter

router = APIRouter()


@router.post("/{argument_id}/vote")
async def vote_argument(argument_id: int):
    """Like an argument (max 3 per case)"""
    return {"message": f"Vote on argument {argument_id} endpoint - implementation pending"}


@router.delete("/{argument_id}/vote")
async def unvote_argument(argument_id: int):
    """Unlike an argument"""
    return {"message": f"Unvote argument {argument_id} endpoint - implementation pending"}
