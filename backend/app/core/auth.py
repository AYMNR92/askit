import os
from supabase import create_client
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path  # <--- INDISPENSABLE

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2. On récupère la vraie clé (plus de valeur par défaut !)
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# 3. Sécurité : On plante immédiatement si la clé manque
if not SECRET_KEY:
    raise ValueError("FATAL : JWT_SECRET_KEY est manquant dans le fichier .env !")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware pour authentifier l'utilisateur dashboard"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("sub")
        if client_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        
        # Vérifier que le client existe et est actif
        client = supabase.table("clients").select("*").eq("id", client_id).eq("is_active", True).single().execute()
        if not client.data:
            raise HTTPException(status_code=401, detail="Client introuvable")
        
        return client.data
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expiré ou invalide")
