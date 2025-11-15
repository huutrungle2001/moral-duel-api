from fastapi import APIRouter

router = APIRouter()


@router.get("/posts")
async def get_community_posts():
    """Get community feed"""
    return {"message": "Community posts endpoint - implementation pending"}


@router.get("/earnings/info")
async def get_earnings_info():
    """Get reward distribution rules"""
    return {
        "distribution": {
            "winning_voters": "40%",
            "top_arguments": "30%",
            "all_participants": "20%",
            "case_creator": "10% (if ≥100 participants)"
        },
        "requirements": {
            "winning_voters": "Must have voted on the winning side",
            "top_arguments": "Top 3 arguments by votes on winning side",
            "all_participants": "All users who voted and submitted an argument",
            "case_creator": "Creator receives reward if case has ≥100 participants"
        }
    }
