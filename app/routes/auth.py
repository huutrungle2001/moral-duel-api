from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from prisma import Prisma
from app.utils.auth import hash_password, verify_password, create_access_token, decode_access_token, get_current_user
from app.utils.database import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

    @validator('name')
    def name_validation(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()


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


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Prisma = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.user.find_unique(where={"email": data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(data.password)
        
        # Create user
        user = await db.user.create(
            data={
                "email": data.email,
                "password": hashed_password,
                "name": data.name,
            }
        )
        
        # Generate token
        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        logger.info(f"User registered: {user.email} (ID: {user.id})")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "neo_wallet_address": user.neo_wallet_address,
                "total_points": user.total_points
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
async def login(data: LoginRequest, db: Prisma = Depends(get_db)):
    """Login user"""
    try:
        # Find user by email
        user = await db.user.find_unique(where={"email": data.email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate token
        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        logger.info(f"User logged in: {user.email} (ID: {user.id})")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "neo_wallet_address": user.neo_wallet_address,
                "total_points": user.total_points
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
