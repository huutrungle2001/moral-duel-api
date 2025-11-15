"""
Transaction Monitor Job

Monitors Neo blockchain transactions for:
- Verdict commitment confirmations
- Reward distribution transactions
- Transaction status updates
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.services.blockchain_service import blockchain_service
from app.utils.database import get_db

logger = logging.getLogger(__name__)


async def monitor_transactions_job():
    """
    Monitor blockchain transactions
    
    Flow:
    1. Find pending reward transactions
    2. Check transaction status on blockchain
    3. Update reward status based on confirmations
    4. Update user points on successful transactions
    5. Retry failed transactions if needed
    """
    try:
        logger.info("Starting transaction monitoring job...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        # Find rewards that are processing (have blockchain TX but not completed)
        processing_rewards = await db.reward.find_many(
            where={
                "status": "processing",
                "blockchain_tx_hash": {"not": None}
            },
            take=100  # Limit to prevent overwhelming the blockchain RPC
        )
        
        if not processing_rewards:
            logger.info("No transactions to monitor")
            return
        
        logger.info(f"Monitoring {len(processing_rewards)} transactions...")
        
        success_count = 0
        failed_count = 0
        pending_count = 0
        
        for reward in processing_rewards:
            try:
                # Get transaction status from blockchain
                tx_status = await blockchain_service.get_transaction(
                    reward.blockchain_tx_hash
                )
                
                if tx_status.get("status") == "confirmed":
                    confirmations = tx_status.get("confirmations", 0)
                    
                    # Consider transaction confirmed after 1+ confirmations
                    if confirmations >= 1:
                        # Update reward to completed
                        await db.reward.update(
                            where={"id": reward.id},
                            data={
                                "status": "completed",
                                "completed_at": datetime.utcnow()
                            }
                        )
                        
                        # Update user total points
                        await db.user.update(
                            where={"id": reward.user_id},
                            data={
                                "total_points": {
                                    "increment": reward.amount
                                }
                            }
                        )
                        
                        success_count += 1
                        logger.info(
                            f"✓ Transaction confirmed: Reward {reward.id}, "
                            f"User {reward.user_id}, Amount {reward.amount}, "
                            f"Confirmations: {confirmations}"
                        )
                    else:
                        pending_count += 1
                        logger.debug(
                            f"Transaction pending: Reward {reward.id}, "
                            f"Confirmations: {confirmations}"
                        )
                        
                elif tx_status.get("status") == "not_found":
                    # Check if transaction is too old (> 24 hours)
                    if reward.updated_at:
                        age = datetime.utcnow() - reward.updated_at
                        if age > timedelta(hours=24):
                            # Mark as failed if transaction missing after 24h
                            await db.reward.update(
                                where={"id": reward.id},
                                data={"status": "failed"}
                            )
                            failed_count += 1
                            logger.warning(
                                f"✗ Transaction not found after 24h: "
                                f"Reward {reward.id}, TX {reward.blockchain_tx_hash}"
                            )
                        else:
                            pending_count += 1
                            
                elif tx_status.get("status") == "error":
                    # Mark as failed
                    await db.reward.update(
                        where={"id": reward.id},
                        data={"status": "failed"}
                    )
                    failed_count += 1
                    logger.error(
                        f"✗ Transaction failed: Reward {reward.id}, "
                        f"Error: {tx_status.get('error')}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Failed to check transaction for reward {reward.id}: {str(e)}"
                )
                continue
        
        logger.info(
            f"✓ Transaction monitoring completed: "
            f"Success={success_count}, Failed={failed_count}, Pending={pending_count}"
        )
        
    except Exception as e:
        logger.error(f"Transaction monitoring job failed: {str(e)}", exc_info=True)


async def check_verdict_transactions_job():
    """
    Check verdict commitment transactions
    
    Verifies that verdict hashes are properly stored on blockchain
    """
    try:
        logger.info("Checking verdict commitment transactions...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        # Find active cases with blockchain TX that haven't been verified
        unverified_cases = await db.case.find_many(
            where={
                "status": "active",
                "blockchain_tx_hash": {"not": None},
                # Could add a "blockchain_verified" field to track this
            },
            take=50
        )
        
        if not unverified_cases:
            logger.info("No verdict transactions to verify")
            return
        
        logger.info(f"Verifying {len(unverified_cases)} verdict transactions...")
        
        verified_count = 0
        
        for case in unverified_cases:
            try:
                verification = await blockchain_service.verify_verdict(
                    case_id=case.id,
                    verdict_hash=case.verdict_hash,
                    blockchain_tx_hash=case.blockchain_tx_hash
                )
                
                if verification.get("verified"):
                    verified_count += 1
                    logger.info(
                        f"✓ Verdict verified on blockchain: Case {case.id}, "
                        f"TX {case.blockchain_tx_hash[:16]}..."
                    )
                else:
                    logger.warning(
                        f"⚠ Verdict verification pending: Case {case.id}, "
                        f"Reason: {verification.get('reason', 'Unknown')}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Failed to verify verdict for case {case.id}: {str(e)}"
                )
                continue
        
        logger.info(
            f"✓ Verdict verification completed: {verified_count} verified"
        )
        
    except Exception as e:
        logger.error(f"Verdict transaction check failed: {str(e)}", exc_info=True)
