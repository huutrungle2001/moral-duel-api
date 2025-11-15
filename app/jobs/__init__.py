"""
Background Job Scheduler for Moral Duel API

Manages scheduled tasks using APScheduler:
- AI case generation (every 12 hours)
- Case closure and verdict revelation (every 5 minutes)
- Transaction monitoring (future)
- Leaderboard updates (future)
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def init_scheduler():
    """Initialize APScheduler instance."""
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler
    
    scheduler = AsyncIOScheduler()
    logger.info("✓ Scheduler initialized")
    return scheduler


def start_scheduler():
    """Start the scheduler and all registered jobs."""
    global scheduler
    
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first")
    
    if scheduler.running:
        logger.warning("Scheduler already running")
        return
    
    scheduler.start()
    logger.info("✓ Scheduler started")


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    
    if scheduler is None or not scheduler.running:
        logger.warning("Scheduler not running")
        return
    
    scheduler.shutdown(wait=True)
    logger.info("✓ Scheduler stopped")


def get_scheduler():
    """Get the scheduler instance."""
    return scheduler
