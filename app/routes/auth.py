from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from prisma import Prisma
from app.utils.auth import hash_password, verify_password, create_access_token, decode_access_token, get_current_user
from app.utils.database import get_db
from app.services.wallet_service import wallet_service
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
async def connect_wallet(
    data: WalletConnectRequest,
    current_user: dict = Depends(get_current_user),
    db: Prisma = Depends(get_db)
):
    """
    Connect Neo wallet to user account
    
    Process:
    1. Verify the signature proves ownership of the Neo address
    2. Check if wallet is already connected to another account
    3. Update user's Neo wallet address
    
    Args:
        data: Wallet connection request (address, signature, message)
        current_user: Authenticated user
        db: Database connection
        
    Returns:
        Connection status
    """
    try:
        # Validate Neo address format
        validation = wallet_service.validate_address(data.neo_address)
        if not validation.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Neo address: {validation.get('reason')}"
            )
        
        # Verify signature
        verification = wallet_service.verify_signature(
            neo_address=data.neo_address,
            message=data.message,
            signature=data.signature
        )
        
        if not verification.get("verified"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Signature verification failed: {verification.get('reason', 'Unknown error')}"
            )
        
        # Check if wallet already connected to another user
        existing_user = await db.user.find_first(
            where={"neo_wallet_address": data.neo_address}
        )
        
        if existing_user and existing_user.id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This wallet is already connected to another account"
            )
        
        # Update user's wallet address
        updated_user = await db.user.update(
            where={"id": current_user["id"]},
            data={"neo_wallet_address": data.neo_address}
        )
        
        logger.info(f"✓ Wallet connected: User {current_user['id']} -> {data.neo_address}")
        
        return {
            "status": "success",
            "message": "Neo wallet successfully connected",
            "neo_address": data.neo_address,
            "user_id": current_user["id"],
            "verification": verification
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wallet connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect wallet: {str(e)}"
        )


@router.get("/wallet/verify")
async def verify_wallet(current_user: dict = Depends(get_current_user)):
    """
    Verify wallet connection and get wallet information
    
    Returns:
    - Connection status
    - Wallet address
    - Balances (NEO, GAS, MORAL tokens)
    
    Args:
        current_user: Authenticated user
        
    Returns:
        Wallet information
    """
    try:
        neo_address = current_user.get("neo_wallet_address")
        
        if not neo_address:
            return {
                "connected": False,
                "message": "No Neo wallet connected to this account"
            }
        
        # Validate address
        validation = wallet_service.validate_address(neo_address)
        if not validation.get("valid"):
            return {
                "connected": False,
                "error": "Connected wallet address is invalid",
                "reason": validation.get("reason")
            }
        
        # Get balance
        balance_info = await wallet_service.get_balance(neo_address)
        
        return {
            "connected": True,
            "neo_address": neo_address,
            "validation": validation,
            "balance": balance_info,
            "user_id": current_user["id"]
        }
        
    except Exception as e:
        logger.error(f"Wallet verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify wallet: {str(e)}"
        )
