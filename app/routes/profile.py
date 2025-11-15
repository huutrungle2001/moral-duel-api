from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_profile():
    """Get user profile with stats"""
    return {"message": "Profile endpoint - implementation pending"}


@router.get("/rewards")
async def list_rewards():
    """List user rewards"""
    return {"message": "Rewards list endpoint - implementation pending"}


@router.post("/rewards/claim")
async def claim_rewards():
    """Claim pending rewards via smart contract"""
    return {"message": "Claim rewards endpoint - implementation pending"}


@router.get("/rewards/{reward_id}/status")
async def get_reward_status(reward_id: int):
    """Check blockchain confirmation status"""
    return {"message": f"Reward {reward_id} status endpoint - implementation pending"}
