from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    NODE_ENV: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "file:./moralduel.db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    
    # Anthropic (optional)
    ANTHROPIC_API_KEY: str = ""
    
    # Google (optional)
    GOOGLE_API_KEY: str = ""
    
    # Neo Blockchain
    NEO_NETWORK: str = "TestNet"
    NEO_RPC_URL: str = "https://testnet1.neo.org:443"
    NEO_PLATFORM_PRIVATE_KEY: str
    NEO_PLATFORM_ADDRESS: str
    NEO_TOKEN_CONTRACT_HASH: str
    NEO_VERDICT_CONTRACT_HASH: str
    
    # Rate Limiting
    RATE_LIMIT_AUTH: int = 5
    RATE_LIMIT_VOTING: int = 10
    RATE_LIMIT_CASE_CREATION: int = 3
    
    # Background Jobs
    AI_CASE_GENERATION_INTERVAL_HOURS: int = 12
    CASE_CLOSURE_INTERVAL_MINUTES: int = 5
    TRANSACTION_MONITOR_INTERVAL_SECONDS: int = 30
    LEADERBOARD_UPDATE_INTERVAL_MINUTES: int = 15
    BADGE_CHECK_INTERVAL_HOURS: int = 1
    
    # Case Configuration
    CASE_DURATION_HOURS: int = 24
    MIN_PARTICIPANTS_FOR_CREATOR_REWARD: int = 100
    
    # Reward Distribution
    REWARD_WINNING_VOTERS_PERCENT: int = 40
    REWARD_TOP_ARGUMENTS_PERCENT: int = 30
    REWARD_ALL_PARTICIPANTS_PERCENT: int = 20
    REWARD_CREATOR_PERCENT: int = 10
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
