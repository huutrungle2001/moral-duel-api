from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.blockchain_service import blockchain_service
from app.utils.database import get_db
from prisma import Prisma

logger = logging.getLogger(__name__)
router = APIRouter()


class VerifyVerdictRequest(BaseModel):
    case_id: int
    verdict_hash: str
    blockchain_tx_hash: str


@router.get("/network-info")
async def get_network_info():
    """
    Get Neo blockchain network status and information
    
    Returns network details including:
    - Connection status
    - Block height
    - Network version
    - Contract addresses
    """
    try:
        network_info = await blockchain_service.get_network_info()
        return network_info
    except Exception as e:
        logger.error(f"Failed to get network info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network info: {str(e)}"
        )


@router.get("/transaction/{tx_hash}")
async def get_transaction(tx_hash: str):
    """
    Get transaction details from Neo blockchain
    
    Args:
        tx_hash: Transaction hash to lookup
        
    Returns:
        Transaction details including confirmations, block height, fees
    """
    try:
        if not tx_hash or len(tx_hash) != 64:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction hash format"
            )
        
        tx_data = await blockchain_service.get_transaction(tx_hash)
        
        if tx_data.get("status") == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found on blockchain"
            )
        
        return tx_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction: {str(e)}"
        )


@router.post("/verify-verdict")
async def verify_verdict(
    request: VerifyVerdictRequest,
    db: Prisma = Depends(get_db)
):
    """
    Verify verdict hash integrity against blockchain
    
    This endpoint checks that:
    1. The case exists in the database
    2. The transaction exists on the blockchain
    3. The verdict hash matches what was committed
    
    Request body:
        case_id: Database case ID
        verdict_hash: Expected verdict hash
        blockchain_tx_hash: Transaction hash to verify
        
    Returns:
        Verification result with blockchain confirmation details
    """
    try:
        # Validate case exists
        case = await db.case.find_unique(
            where={"id": request.case_id}
        )
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {request.case_id} not found"
            )
        
        # Check if case has blockchain transaction
        if not case.blockchain_tx_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case does not have a blockchain transaction"
            )
        
        # Verify the provided tx_hash matches the case
        if case.blockchain_tx_hash != request.blockchain_tx_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction hash does not match case record"
            )
        
        # Verify verdict hash against blockchain
        verification = await blockchain_service.verify_verdict(
            case_id=request.case_id,
            verdict_hash=request.verdict_hash,
            blockchain_tx_hash=request.blockchain_tx_hash
        )
        
        return {
            "case_id": request.case_id,
            "case_title": case.title,
            "case_status": case.status,
            "verdict_hash_database": case.verdict_hash,
            "verdict_hash_provided": request.verdict_hash,
            "blockchain_tx_hash": request.blockchain_tx_hash,
            "verification": verification,
            "hashes_match": case.verdict_hash == request.verdict_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verdict verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/case/{case_id}/blockchain")
async def get_case_blockchain_info(
    case_id: int,
    db: Prisma = Depends(get_db)
):
    """
    Get blockchain information for a specific case
    
    Args:
        case_id: Case ID
        
    Returns:
        Blockchain details including transaction hash, verdict hash, and verification status
    """
    try:
        case = await db.case.find_unique(
            where={"id": case_id}
        )
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case {case_id} not found"
            )
        
        result = {
            "case_id": case.id,
            "case_title": case.title,
            "case_status": case.status,
            "verdict_hash": case.verdict_hash,
            "blockchain_tx_hash": case.blockchain_tx_hash,
            "has_blockchain_commitment": bool(case.blockchain_tx_hash)
        }
        
        # If case has blockchain transaction, get transaction details
        if case.blockchain_tx_hash:
            try:
                tx_data = await blockchain_service.get_transaction(case.blockchain_tx_hash)
                result["transaction"] = tx_data
            except Exception as e:
                logger.error(f"Failed to fetch transaction details: {str(e)}")
                result["transaction"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # If case is closed, include verdict reveal info
        if case.status == "closed":
            result["ai_verdict"] = case.ai_verdict
            result["ai_confidence"] = case.ai_confidence
            result["closed_at"] = case.closed_at
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case blockchain info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blockchain info: {str(e)}"
        )

