import os
import json
import redis
import asyncio
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from fastapi import HTTPException, Request, Header
from supabase import create_client

# 1. Connexion aux services
# On récupère les vars depuis l'environnement (chargé par main.py)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
REDIS_URL = os.getenv("REDIS_URL")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase creds manquants")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gestion Graceful de Redis (si pas de Redis, on fera sans cache/rate-limit)
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"⚠️ Erreur init Redis: {e}")

executor = ThreadPoolExecutor(max_workers=5)

# --- FONCTIONS UTILITAIRES ---

def is_origin_allowed(origin: str, allowed_list: list) -> bool:
    """Vérification robuste avec wildcard support (*.domaine.com)"""
    try:
        if not origin: return False
        # On ajoute https:// si manquant pour que urlparse fonctionne
        parsed = urlparse(origin if origin.startswith('http') else f"https://{origin}")
        domain = (parsed.netloc or parsed.path).split(':')[0].lower()
        
        print(f"🔍 Check Domaine: Reçu='{domain}' vs Autorisés={allowed_list}")

        # 1. Exact match
        if domain in allowed_list: return True
        
        # 2. Wildcard (*.example.com)
        for allowed in allowed_list:
            if allowed.startswith('*.') and domain.endswith(allowed[2:]):
                return True
        return False
    except Exception as e:
        print(f"⚠️ Erreur parsing domaine: {e}")
        return False

async def log_security_violation(client_id: str, origin: str, reason: str):
    """Log non-bloquant dans Supabase"""
    def _log():
        try:
            supabase.table("security_logs").insert({
                "client_id": client_id,
                "domain_detected": origin,
                "reason": reason
            }).execute()
        except: pass
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, _log)

async def increment_usage_async(client_id: str):
    """Incrémenter le quota en arrière-plan (Fire-and-forget)"""
    def _increment():
        try:
            # Option A: Redis (si dispo)
            if redis_client:
                redis_client.incr(f"quota:{client_id}")
            # Option B: Supabase (plus lent mais persistant)
            # Dans une vraie prod, on synchronise Redis -> Supabase toutes les 5min.
            # Ici pour ton MVP, on fait l'update direct mais dans un thread séparé pour ne pas ralentir l'IA.
            supabase.table("clients").rpc("increment_usage", {"row_id": client_id}).execute() 
            # (Note: Assure-toi d'avoir créé la fonction SQL increment_usage ou utilise un .update simple)
            
            # Fallback simple si RPC n'existe pas :
            # current = supabase.table("clients").select("requests_used").eq("id", client_id).single().execute()
            # new_val = current.data['requests_used'] + 1
            # supabase.table("clients").update({"requests_used": new_val}).eq("id", client_id).execute()
        except: pass

    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, _increment)

async def get_client_data_cached(token: str) -> dict:
    cache_key = f"client:{token}"
    
    # 1. Essayer Redis
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached: return json.loads(cached)
        except: pass 
    
    # 2. Supabase
    print(f"🔍 Recherche Token en DB : {token}")
    response = supabase.table("clients").select("*").eq("public_token", token).eq("is_active", True).execute()
    
    if not response.data:
        print("❌ Token non trouvé dans Supabase !")
        return None
    
    client_data = response.data[0]
    
    # # 3. Sauver dans Redis (1 heure)
    # if redis_client:
    #     try:
    #         redis_client.setex(cache_key, 3600, json.dumps(client_data))
    #     except: pass
        
    return client_data

# --- LE MIDDLEWARE PRINCIPAL ---

async def verify_security(
    request: Request,
    x_widget_token: str = Header(None, alias="X-Widget-Token")
):
    print("\n--- 🛡️ VIGILE SECURITY CHECK ---")
    
    # 1. TOKEN
    print(f"👉 Token reçu : '{x_widget_token}'")

    if not x_widget_token:
        print("❌ Rejet: Pas de header X-Widget-Token")
        raise HTTPException(401, "Token manquant (X-Widget-Token)")
    
    client_data = await get_client_data_cached(x_widget_token)
    if not client_data:
        print("❌ Rejet: Client introuvable pour ce token")
        raise HTTPException(403, "Token invalide ou client inactif")
    
    # 2. DOMAINE (ORIGIN)
    origin = request.headers.get("origin") or request.headers.get("referer")
    print(f"👉 Origine détectée : '{origin}'")
    # On autorise localhost et 127.0.0.1 pour tes tests, sinon c'est l'enfer
    # is_local = origin and ("localhost" in origin or "127.0.0.1" in origin)
    
    # if origin and not is_local:
    #     if not is_origin_allowed(origin, client_data['allowed_origins']):
    #         await log_security_violation(client_data['id'], origin, "Domain mismatch")
    #         raise HTTPException(403, f"Domaine non autorisé: {origin}")
    print("✅ Accès autorisé (Check domaine désactivé temporairement)")
            
    # 3. RATE LIMITING (Via Redis)
    if redis_client:
        client_ip = request.client.host
        rate_key = f"rate:{x_widget_token}:{client_ip}"
        try:
            count = redis_client.incr(rate_key)
            if count == 1: redis_client.expire(rate_key, 60)
            if count > 20: raise HTTPException(429, "Trop de requêtes. (Max 20/min)")
        except redis.RedisError:
            pass # Graceful degradation
            
    # 4. QUOTA VERIFICATION
    # On vérifie juste le quota connu dans le cache client_data pour aller vite
    if client_data['requests_used'] >= client_data['monthly_quota']:
        print("❌ Rejet: Quota dépassé")
        raise HTTPException(402, "Quota mensuel dépassé.")
        
    return client_data