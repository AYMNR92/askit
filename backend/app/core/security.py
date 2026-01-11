import os
import json
import redis
import asyncio
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from fastapi import HTTPException, Request, Header
from supabase import create_client

# 1. Connexion aux services
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase creds manquants")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gestion Graceful de Redis
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception:
        pass # On continue sans cache si Redis n'est pas là

executor = ThreadPoolExecutor(max_workers=5)

# --- FONCTIONS UTILITAIRES ---

def is_origin_allowed(origin: str, allowed_list: list) -> bool:
    try:
        if not origin: return False
        parsed = urlparse(origin if origin.startswith('http') else f"https://{origin}")
        domain = (parsed.netloc or parsed.path).split(':')[0].lower()
        
        if domain in allowed_list: return True
        for allowed in allowed_list:
            if allowed.startswith('*.') and domain.endswith(allowed[2:]):
                return True
        return False
    except:
        return False

async def increment_usage_async(client_id: str):
    def _increment():
        try:
            if redis_client:
                redis_client.incr(f"quota:{client_id}")
            supabase.table("clients").rpc("increment_usage", {"row_id": client_id}).execute() 
        except: pass
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, _increment)

async def get_client_data_cached(token: str) -> dict:
    cache_key = f"client:{token}"
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached: return json.loads(cached)
        except: pass 
    
    response = supabase.table("clients").select("*").eq("public_token", token).eq("is_active", True).execute()
    
    if not response.data:
        return None
    
    client_data = response.data[0]
    
    if redis_client:
        try:
            redis_client.setex(cache_key, 3600, json.dumps(client_data))
        except: pass
        
    return client_data

# --- LE MIDDLEWARE PRINCIPAL ---

async def verify_security(
    request: Request,
    x_widget_token: str = Header(None, alias="X-Widget-Token")
):
    # 1. TOKEN
    if not x_widget_token:
        raise HTTPException(401, "Token manquant (X-Widget-Token)")
    
    client_data = await get_client_data_cached(x_widget_token)
    if not client_data:
        raise HTTPException(403, "Token invalide ou client inactif")
    
    # 2. DOMAINE (ORIGIN) - RÉACTIVÉ
    origin = request.headers.get("origin") or request.headers.get("referer")
    # On autorise localhost pour tes tests
    is_local = origin and ("localhost" in origin or "127.0.0.1" in origin)
    
    if origin and not is_local:
        # On vérifie vraiment si le domaine est dans la liste
        if not is_origin_allowed(origin, client_data['allowed_origins']):
             # Tu peux décommenter la ligne suivante pour loguer les tentatives
             # await log_security_violation(client_data['id'], origin, "Domain mismatch")
             raise HTTPException(403, f"Domaine non autorisé: {origin}")
            
    # 3. RATE LIMITING
    if redis_client:
        client_ip = request.client.host
        rate_key = f"rate:{x_widget_token}:{client_ip}"
        try:
            count = redis_client.incr(rate_key)
            if count == 1: redis_client.expire(rate_key, 60)
            if count > 20: raise HTTPException(429, "Trop de requêtes. (Max 20/min)")
        except redis.RedisError:
            pass
            
    # 4. QUOTA
    if client_data['requests_used'] >= client_data['monthly_quota']:
        raise HTTPException(402, "Quota mensuel dépassé.")
        
    return client_data