from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.utils.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class WalletConnectRequest(BaseModel):
    neo_address: str
    signature: str
    message: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register", response_model=AuthResponse)
async def register(data: RegisterRequest):
    """Register a new user"""
    # TODO: Implement with database once Prisma client is generated
    try:
        # Validate password
        if len(data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Generate token (mock user for now)
        token = create_access_token(data={"sub": "1", "email": data.email})
        
        logger.info(f"User registered (mock): {data.email}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": data.email,
                "name": data.name,
                "neo_wallet_address": None,
                "total_points": 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest):
    """Login user"""
    # TODO: Implement with database once Prisma client is generated
    try:
        # Generate token (mock user for now)
        token = create_access_token(data={"sub": "1", "email": data.email})
        
        logger.info(f"User logged in (mock): {data.email}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": 1,
                "email": data.email,
                "name": "Test User",
                "neo_wallet_address": None,
                "total_points": 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/wallet/connect")
async def connect_wallet(data: WalletConnectRequest):
    """Connect Neo wallet to user account"""
    # TODO: Implement Neo wallet signature verification
    return {
        "status": "success",
        "message": "Wallet connection endpoint - implementation pending"
    }


@router.get("/wallet/verify")
async def verify_wallet():
    """Verify wallet connection and balance"""
    # TODO: Implement wallet verification
    return {
        "status": "success",
        "message": "Wallet verification endpoint - implementation pending"
    }
