import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# --- Imports des services ---
from app.services.rag import add_knowledge_to_db, search_knowledge_base, get_all_conversations, save_conversation
from app.services.scraper import scrape_website
# Utilisation du nouveau module
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

# --- Imports de Sécurité (LES DEUX VIGILES) ---
from app.core.security import verify_security, increment_usage_async, supabase  # Vigile Widget
from app.core.auth import get_current_user, create_access_token, verify_password # Vigile Dashboard

app = FastAPI()

# Configuration CORS (Vital pour que le Dashboard et le Widget fonctionnent)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation LLM (si pas fait ailleurs)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY"))

# --- MODÈLES PYDANTIC ---
class LearnRequest(BaseModel):
    text: str

class ScrapeRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    question: str # Le widget envoie "question" (suite à notre fix précédent)

# ==========================================
# 🔐 ROUTE D'AUTHENTIFICATION (PUBLIQUE)
# ==========================================
@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"👉 1. Tentative de connexion reçue pour : '{form_data.username}'")
    print(f"👉 2. Mot de passe reçu : '{form_data.password}'")

    # 1. On cherche le client dans la BDD
    response = supabase.table("clients").select("*").eq("email", form_data.username).eq("is_active", True).execute()
    
    # DEBUG : Voir ce que Supabase renvoie
    print(f"👉 3. Résultat DB : {response.data}")

    # 2. Vérification existence
    if not response.data:
        print("❌ ERREUR : Aucun utilisateur trouvé avec cet email.")
        raise HTTPException(status_code=401, detail="Email inconnu")
    
    client = response.data[0]
    print(f"👉 4. Hash en base : {client['password_hash']}")
    
    # 3. Vérification mot de passe
    is_valid = verify_password(form_data.password, client['password_hash'])
    print(f"👉 5. Résultat vérification mot de passe : {is_valid}")

    if not is_valid:
        print("❌ ERREUR : Le mot de passe ne correspond pas au hash.")
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    
    print("✅ SUCCÈS : Token généré.")
    
    # 4. Création du Token JWT
    access_token = create_access_token(data={"sub": client['id']})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "client": {
            "id": client['id'],
            "name": client['name'],
            "email": client['email']
        }
    }

# ==========================================
# 🏢 ROUTES DASHBOARD (Vigile: get_current_user)
# ==========================================

@app.get("/api/history")
def history_endpoint(client_data: dict = Depends(get_current_user)): # <--- JWT requis
    """Récupère l'historique (Admin seulement)"""
    try:
        return get_all_conversations(client_id=client_data['id'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learn")
def learn_endpoint(request: LearnRequest, client_data: dict = Depends(get_current_user)): # <--- JWT requis
    """Apprentissage manuel (Admin seulement)"""
    try:
        add_knowledge_to_db(request.text, client_id=client_data['id'])
        return {"message": "Information apprise avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
def scrape_endpoint(request: ScrapeRequest, client_data: dict = Depends(get_current_user)): # <--- JWT requis
    """Scraping de site web (Admin seulement)"""
    try:
        print(f"1. Aspiration pour {client_data['name']} : {request.url}")
        raw_text = scrape_website(request.url)
        
        if not raw_text: 
            raise HTTPException(status_code=400, detail="Page vide.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(raw_text)
        
        for i, chunk in enumerate(chunks):
            source_info = f"{request.url} (Partie {i+1}/{len(chunks)})"
            add_knowledge_to_db(chunk, client_id=client_data['id'], source=source_info)
        
        return {"message": f"Succès ! {len(chunks)} morceaux ajoutés pour {client_data['name']}."}
    except Exception as e:
        print(f"Erreur Scrape : {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 💬 ROUTE WIDGET (Vigile: verify_security)
# ==========================================

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, client_data: dict = Depends(verify_security)): # <--- Widget Token requis
    """Discussion publique avec le bot (Sécurisée par Token Widget & CORS)"""
    try:
        client_id = client_data['id']
        
        # 1. RECHERCHE ISOLÉE
        context_results = search_knowledge_base(request.question, client_id=client_id)

        print(f"\n🔍 QUESTION : {request.question}")
        print(f"📦 CONTEXTE TROUVÉ ({len(context_results)} documents) :")
        for idx, doc in enumerate(context_results):
            print(f"   --- Doc {idx+1} : {doc[:100]}...") # On affiche les 100 premiers caractères
        print("--------------------------------------------------\n")
        
        context_text = "\n\n".join(context_results) if context_results else "Aucune information spécifique trouvée."

        # 2. PROMPT
        system_prompt = f"""Tu es l'assistant de {client_data['name']}.
        Utilise UNIQUEMENT le contexte ci-dessous pour répondre.
        Si la réponse n'est pas dans le contexte, dis poliment que tu ne sais pas.
        CONTEXTE: {context_text}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.question)
        ]
        
        # 3. GENERATION
        response = llm.invoke(messages)
        
        # 4. QUOTA & SAUVEGARDE
        await increment_usage_async(client_id)
        save_conversation(request.question, response.content, client_id=client_id)
        
        return {
            "response": response.content,
            "sources": context_results
        }

    except Exception as e:
        print(f"Erreur Chat : {e}")
        raise HTTPException(status_code=500, detail=str(e))