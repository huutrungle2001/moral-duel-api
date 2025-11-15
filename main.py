from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from contextlib import asynccontextmanager

from app.config import settings
from app.routes import auth, cases, arguments, profile, blockchain, leaderboard, community
from app.middleware.rate_limiter import RateLimitMiddleware
from app.utils.database import init_db, disconnect_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry if configured
if settings.SENTRY_DSN and settings.SENTRY_DSN.startswith("http"):
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        environment=settings.NODE_ENV,
        traces_sample_rate=1.0 if settings.NODE_ENV == "development" else 0.1,
    )
    logger.info("Sentry monitoring initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Moral Duel API...")
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Moral Duel API...")
    await disconnect_db()
    logger.info("Database disconnected")


# Create FastAPI app
app = FastAPI(
    title="Moral Duel API",
    description="Blockchain-powered debate platform with AI-driven moral verdicts",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(cases.router, prefix="/cases", tags=["Cases"])
app.include_router(arguments.router, prefix="/arguments", tags=["Arguments"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(blockchain.router, prefix="/blockchain", tags=["Blockchain"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
app.include_router(community.router, prefix="/community", tags=["Community"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Moral Duel API is running",
        "version": "1.0.0",
        "environment": settings.NODE_ENV
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "blockchain": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
