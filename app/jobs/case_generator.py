"""
Background Jobs for Case Management

Jobs:
1. AI Case Generator - Runs every 12 hours to generate new cases
2. Case Closer - Runs every 5 minutes to close expired cases
"""
import logging
from datetime import datetime
from apscheduler.triggers.interval import IntervalTrigger
from app.services.ai_service import ai_service
from app.services.blockchain_service import blockchain_service
from app.services.reward_service import reward_service
from app.utils.database import get_db

logger = logging.getLogger(__name__)


async def generate_ai_case_job():
    """
    Generate AI case with pre-committed verdict.
    
    Flow:
    1. Generate moral dilemma using AI
    2. Generate AI verdict
    3. Hash the verdict
    4. Commit verdict hash to blockchain
    5. Store case with hidden verdict and blockchain TX hash
    6. Set 24-hour timer
    """
    try:
        logger.info("Starting AI case generation job...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        # Generate complete case with verdict
        case_data = await ai_service.generate_case_with_verdict()
        
        # Commit verdict hash to blockchain BEFORE creating the case
        blockchain_tx = None
        try:
            blockchain_tx = await blockchain_service.commit_verdict_hash(
                case_id=0,  # Temporary, will update after case creation
                verdict_hash=case_data["verdict_hash"],
                verdict=case_data["verdict"],
                closes_at=case_data["closes_at"]
            )
            logger.info(f"✓ Verdict committed to blockchain: TX={blockchain_tx.get('tx_hash', 'N/A')[:16]}...")
        except Exception as e:
            logger.error(f"Blockchain commitment failed (continuing with case creation): {str(e)}")
            # Continue with case creation even if blockchain fails
        
        # Create case in database
        case = await db.case.create(
            data={
                "title": case_data["title"],
                "context": case_data["context"],
                "status": case_data["status"],
                "ai_verdict": case_data["verdict"],
                "ai_verdict_reasoning": case_data["verdict_reasoning"],
                "ai_confidence": case_data["verdict_confidence"],
                "verdict_hash": case_data["verdict_hash"],
                "blockchain_tx_hash": blockchain_tx.get("tx_hash") if blockchain_tx else None,
                "closes_at": case_data["closes_at"],
                "is_ai_generated": True,
                "yes_votes": 0,
                "no_votes": 0,
                "total_participants": 0
            }
        )
        
        logger.info(
            f"✓ AI case generated: ID={case.id}, "
            f"Title='{case.title[:50]}...', "
            f"Verdict={case_data['verdict']} (hidden), "
            f"Blockchain TX={case.blockchain_tx_hash[:16] if case.blockchain_tx_hash else 'None'}..., "
            f"Closes at {case_data['closes_at']}"
        )
        
    except Exception as e:
        logger.error(f"AI case generation job failed: {str(e)}", exc_info=True)


async def close_expired_cases_job():
    """
    Close cases that have reached their expiration time.
    
    Flow:
    1. Find cases where closes_at <= NOW()
    2. Update status to 'closed'
    3. Reveal AI verdict
    4. Calculate rewards (future)
    5. Mark top 3 arguments (future)
    """
    try:
        logger.info("Starting case closure job...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        # Find expired cases
        now = datetime.utcnow()
        cases_to_close = await db.case.find_many(
            where={
                "status": "active",
                "closes_at": {
                    "lte": now
                }
            }
        )
        
        if not cases_to_close:
            logger.info("No cases to close")
            return
        
        logger.info(f"Found {len(cases_to_close)} cases to close")
        
        for case in cases_to_close:
            try:
                # Get all arguments for this case, sorted by votes
                arguments = await db.argument.find_many(
                    where={"case_id": case.id},
                    order={"votes": "desc"}
                )
                
                # Mark top 3 arguments
                top_3_ids = [arg.id for arg in arguments[:3]]
                if top_3_ids:
                    await db.argument.update_many(
                        where={"id": {"in": top_3_ids}},
                        data={"is_top_3": True}
                    )
                    logger.info(f"Marked {len(top_3_ids)} top arguments for case {case.id}")
                
                # Close the case
                await db.case.update(
                    where={"id": case.id},
                    data={
                        "status": "closed",
                        "closed_at": now
                    }
                )
                
                logger.info(
                    f"✓ Case {case.id} closed: "
                    f"Verdict={case.ai_verdict}, "
                    f"YES={case.yes_votes}, NO={case.no_votes}, "
                    f"Arguments={len(arguments)}, Top 3 marked={len(top_3_ids)}"
                )
                
                # Calculate and distribute rewards
                try:
                    logger.info(f"Calculating rewards for case {case.id}...")
                    reward_calc = await reward_service.calculate_rewards(db, case)
                    
                    if reward_calc.get("distributions"):
                        # Create reward records
                        rewards = await reward_service.create_reward_records(
                            db,
                            case.id,
                            reward_calc["distributions"]
                        )
                        logger.info(
                            f"✓ Rewards calculated: {len(rewards)} users rewarded, "
                            f"Total pool: {reward_calc['reward_pool']:.2f}"
                        )
                    else:
                        logger.info(f"No rewards to distribute for case {case.id}")
                        
                except Exception as e:
                    logger.error(f"Failed to calculate rewards for case {case.id}: {str(e)}")
                    # Don't fail case closure if rewards fail
                
                # TODO: Verify verdict against blockchain
                
            except Exception as e:
                logger.error(f"Failed to close case {case.id}: {str(e)}")
                continue
        
        logger.info(f"✓ Case closure completed: {len(cases_to_close)} cases closed")
        
    except Exception as e:
        logger.error(f"Case closure job failed: {str(e)}", exc_info=True)


def register_jobs(scheduler):
    """
    Register all background jobs with the scheduler.
    
    Args:
        scheduler: APScheduler instance
    """
    # AI Case Generation - every 12 hours
    scheduler.add_job(
        generate_ai_case_job,
        trigger=IntervalTrigger(hours=12),
        id="ai_case_generation",
        name="Generate AI moral dilemma cases",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✓ Registered: AI case generation (every 12 hours)")
    
    # Case Closure - every 5 minutes
    scheduler.add_job(
        close_expired_cases_job,
        trigger=IntervalTrigger(minutes=5),
        id="case_closure",
        name="Close expired cases",
        replace_existing=True,
        max_instances=1
    )
    logger.info("✓ Registered: Case closure (every 5 minutes)")
    
    # TODO: Transaction monitoring (every 30 seconds)
    # TODO: Leaderboard update (every 15 minutes)
    
    logger.info("✓ All background jobs registered")
