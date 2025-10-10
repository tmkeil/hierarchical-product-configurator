"""
JWT Authentication Module für Variantenbaum API

Enthält:
- JWT Token Generation/Validation
- Password Hashing/Verification
- User Authentication Dependencies
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os

# ============================================================
# Configuration
# ============================================================

# JWT Settings (aus Environment Variables)
SECRET_KEY = os.getenv("JWT_SECRET", "development-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

# Password Hashing (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security Scheme für FastAPI Docs
security = HTTPBearer()

# ============================================================
# Pydantic Models
# ============================================================

class TokenData(BaseModel):
    """JWT Token Payload"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class Token(BaseModel):
    """Token Response"""
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    """User Model (ohne password_hash!)"""
    id: int
    username: str
    role: str
    is_active: bool
    must_change_password: bool
    created_at: str

class UserInDB(User):
    """User Model mit password_hash (nur intern!)"""
    password_hash: str

class LoginRequest(BaseModel):
    """Login Request"""
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    """Change Password Request"""
    old_password: str
    new_password: str

# ============================================================
# Password Hashing
# ============================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifiziert Passwort gegen Hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hasht Passwort mit bcrypt"""
    return pwd_context.hash(password)

# ============================================================
# JWT Token Functions
# ============================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Erstellt JWT Access Token
    
    Args:
        data: Payload Data (username, user_id, role)
        expires_delta: Optional custom expiration time
        
    Returns:
        str: JWT Token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def decode_access_token(token: str) -> TokenData:
    """
    Dekodiert und validiert JWT Token
    
    Args:
        token: JWT Token String
        
    Returns:
        TokenData: Dekodierte Token Daten
        
    Raises:
        HTTPException: Wenn Token invalid oder abgelaufen
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id, role=role)
        return token_data
        
    except JWTError:
        raise credentials_exception

# ============================================================
# Authentication Dependencies
# ============================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    Dependency: Validiert JWT Token und gibt User zurück
    
    Usage:
        @app.get("/protected", dependencies=[Depends(get_current_user)])
        async def protected_route():
            ...
    """
    token = credentials.credentials
    return decode_access_token(token)

async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency: Prüft ob User aktiv ist
    """
    # Hier könnten wir zusätzlich in DB prüfen ob User aktiv ist
    # Für jetzt: Token-Validation reicht
    return current_user

async def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency: Nur Admins erlaubt
    
    Usage:
        @app.post("/admin/users", dependencies=[Depends(require_admin)])
        async def create_user():
            ...
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
