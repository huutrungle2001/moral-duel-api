from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_leaderboard():
    """Get top users by points"""
    return {"message": "Leaderboard endpoint - implementation pending"}
