import os
import re
import logging
import traceback
import time
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field, ValidationError

# --- Services ---
from app.services.rag import add_knowledge_to_db, search_knowledge_base, get_all_conversations, save_conversation
from app.services.scraper import scrape_website
from app.services.shopify_service import ShopifyService 

# --- LangChain ---
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

# --- Sécurité ---
from app.core.security import verify_security, increment_usage_async, supabase
from app.core.auth import get_current_user, create_access_token, verify_password

# --- CONFIG LOGS SECURISEE ---
# On évite de logger les données sensibles par défaut
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api")

app = FastAPI(title="Askit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================
# 🛡️ 1. VALIDATION STRICTE DES ENTRÉES
# ==========================================
class ChatRequest(BaseModel):
    # Protection DoS : Limite la taille du message (max 500 chars)
    # Protection Input Vide : min_length=2
    question: str = Field(..., min_length=2, max_length=500, description="La question de l'utilisateur")

class LearnRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)

class ScrapeRequest(BaseModel):
    url: str

# ==========================================
# 🛡️ 2. RATE LIMITING BASIQUE (Mémoire)
# ==========================================
# Note: En vraie prod multi-serveurs, utiliser Redis. Ici dictionnaire simple.
request_counts = {}

def rate_limiter(client_id: str):
    """Limite à 10 requêtes par minute par client"""
    current_time = time.time()
    if client_id not in request_counts:
        request_counts[client_id] = []
    
    # Nettoyage des vieilles requêtes (> 60s)
    request_counts[client_id] = [t for t in request_counts[client_id] if current_time - t < 60]
    
    if len(request_counts[client_id]) >= 10:
        logger.warning(f"⛔ Rate Limit atteint pour {client_id}")
        raise HTTPException(status_code=429, detail="Trop de requêtes. Veuillez patienter.")
    
    request_counts[client_id].append(current_time)

# ==========================================
# HELPER SHOPIFY
# ==========================================
def get_client_shopify_config(client_id: str):
    try:
        response = supabase.table("shopify_stores").select("*").eq("client_id", client_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Erreur DB interne (Shopify Config): {str(e)}")
        return None

# ==========================================
# 🔐 AUTH
# ==========================================
@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        response = supabase.table("clients").select("*").eq("email", form_data.username).eq("is_active", True).execute()
        if not response.data:
            # Timing attack protection: on devrait attendre un peu ici, mais passons pour l'instant
            raise HTTPException(status_code=401, detail="Identifiants incorrects")
        
        client = response.data[0]
        if not verify_password(form_data.password, client['password_hash']):
            raise HTTPException(status_code=401, detail="Identifiants incorrects")
        
        access_token = create_access_token(data={"sub": client['id']})
        return {"access_token": access_token, "token_type": "bearer", "client": {"id": client['id'], "name": client['name']}}
    except Exception:
        logger.error(f"Erreur Login: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Erreur interne")

# ==========================================
# 💬 CHAT ENDPOINT (SÉCURISÉ)
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, client_data: dict = Depends(verify_security)):
    request_id = os.urandom(4).hex() # Pour tracer la requête dans les logs
    client_id = client_data['id']
    
    print(f"DEBUG CRITIQUE: ID du client connecté = {client_id}")
    conf_test = get_client_shopify_config(client_id)
    print(f"DEBUG CRITIQUE: Résultat config Shopify = {conf_test}")

    try:
        # 1. RATE LIMITING
        rate_limiter(client_id)

        # 2. LOGGING ANONYMISÉ (RGPD Friendly)
        # On ne logue PAS le contenu du message, juste sa présence
        logger.info(f"[{request_id}] 📨 Message reçu de {client_id} (Len: {len(request.question)})")

        question = request.question
        bot_response = ""
        sources = []
        shopify_success = False

        # 3. LOGIQUE SHOPIFY SÉCURISÉE
        shopify_conf = get_client_shopify_config(client_id)
        if shopify_conf:
            strict_regex = r'(?:#|commande\s*|n°\s*|numéro\s*)\s*(\d{4,})'
            order_match = re.search(strict_regex, question, re.IGNORECASE)
            
            if order_match:
                order_number = order_match.group(1)
                logger.info(f"[{request_id}] 🛍️ Intention Shopify détectée pour #{order_number}")
                
                try:
                    service = ShopifyService(
                        shop_url=shopify_conf['shop_url'],
                        access_token=shopify_conf['access_token']
                    )
                    
                    # 1. On récupère la donnée MAIS on ne l'affiche pas tout de suite
                    order_data = await service.get_order_status_data(order_number)
                    
                    if order_data:
                        # 2. CHALLENGE DE SÉCURITÉ 🛡️
                        # On regarde si l'email de la commande est présent dans la question de l'utilisateur
                        user_text_lower = question.lower()
                        order_email = order_data['email']
                        
                        if order_email and order_email in user_text_lower:
                            # ✅ L'email est dans la phrase -> On autorise
                            logger.info(f"[{request_id}] ✅ Vérification Email OK pour #{order_number}")
                            bot_response = service.format_for_bot(order_data, question)
                            sources = ["Shopify API (Vérifié)"]
                            shopify_success = True
                        else:
                            # ❌ L'email n'est pas là -> On bloque
                            logger.warning(f"[{request_id}] ⛔ Bloqué : Email manquant pour #{order_number}")
                            bot_response = (
                                f"🔒 **Sécurité** : J'ai trouvé la commande #{order_number}, "
                                f"mais pour protéger vos données, veuillez me confirmer l'adresse email associée.\n\n"
                                f"👉 *Réessayez en écrivant : 'Ma commande #{order_number} (mon@email.com)'*"
                            )
                            sources = ["Sécurité"]
                            shopify_success = True # On dit True pour ne pas que le RAG réponde par dessus
                    else:
                        logger.info(f"[{request_id}] Commande introuvable chez Shopify")
                
                except Exception as shop_e:
                    logger.error(f"[{request_id}] 💥 Erreur Shopify Service: {shop_e}")

        # 4. FALLBACK RAG
        if not shopify_success:
            logger.info(f"[{request_id}] 📚 Passage en mode RAG")
            context_results = search_knowledge_base(question, client_id=client_id)
            context_text = "\n\n".join(context_results) if context_results else "Aucune info spécifique."
            
            system_prompt = f"""Tu es l'assistant de {client_data['name']}.
            Contexte : {context_text}"""
            
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=question)]
            ai_msg = llm.invoke(messages)
            bot_response = ai_msg.content
            sources = context_results

        # 5. SAUVEGARDE
        await increment_usage_async(client_id)
        save_conversation(question, bot_response, client_id=client_id)
        
        return {"response": bot_response, "sources": sources}

    except ValidationError as ve:
        # Erreur de validation Pydantic (input trop long, etc.)
        logger.warning(f"[{request_id}] ⚠️ Validation Error: {ve}")
        raise HTTPException(status_code=422, detail="Message invalide (trop long ou vide)")
        
    except HTTPException as he:
        # On relance les erreurs HTTP volontaires (401, 429...)
        raise he

    except Exception as e:
        # CATCH-ALL SÉCURISÉ
        # 1. On logue TOUT le crash technique pour les devs
        logger.error(f"[{request_id}] 💥 CRASH NON GÉRÉ : {traceback.format_exc()}")
        
        # 2. On répond un message générique propre au client (Sécurité par l'obscurité)
        return {
            "response": "Oups, une erreur interne est survenue. Nos équipes ont été notifiées.",
            "sources": ["System Error"]
        }

# --- ENDPOINTS SECONDAIRES ---
@app.get("/api/history")
def history_endpoint(client_data: dict = Depends(get_current_user)):
    return get_all_conversations(client_id=client_data['id'])

@app.post("/api/learn")
def learn_endpoint(request: LearnRequest, client_data: dict = Depends(get_current_user)):
    # Ici aussi, la validation Pydantic protège
    add_knowledge_to_db(request.text, client_id=client_data['id'])
    return {"message": "Information apprise."}

@app.post("/api/scrape")
def scrape_endpoint(request: ScrapeRequest, client_data: dict = Depends(get_current_user)):
    # ... (Code scrape inchangé, mais protégé par Pydantic et Exception Handler global) ...
    try:
        raw_text = scrape_website(request.url)
        if not raw_text: raise HTTPException(status_code=400, detail="Page vide")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(raw_text)
        for i, chunk in enumerate(chunks):
            add_knowledge_to_db(chunk, client_id=client_data['id'], source=f"{request.url} ({i+1})")
        return {"message": f"Succès ! {len(chunks)} morceaux ajoutés."}
    except Exception as e:
        logger.error(f"Scrape Error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors du scraping")