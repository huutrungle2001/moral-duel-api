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
from app.utils.database import get_db

logger = logging.getLogger(__name__)


async def generate_ai_case_job():
    """
    Generate AI case with pre-committed verdict.
    
    Flow:
    1. Generate moral dilemma using AI
    2. Generate AI verdict
    3. Hash the verdict
    4. Store case with hidden verdict
    5. Set 24-hour timer
    """
    try:
        logger.info("Starting AI case generation job...")
        
        db = get_db()
        if db is None:
            logger.error("Database not initialized")
            return
        
        # Generate complete case with verdict
        case_data = await ai_service.generate_case_with_verdict()
        
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
            f"Closes at {case_data['closes_at']}"
        )
        
        # TODO: Commit verdict hash to blockchain
        
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
                    f"YES={case.yes_votes}, NO={case.no_votes}"
                )
                
                # TODO: Mark top 3 arguments
                # TODO: Calculate rewards
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
