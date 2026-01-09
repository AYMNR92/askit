import os
import pathlib
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi.middleware.cors import CORSMiddleware
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Configuration des chemins (.env)
basedir = pathlib.Path(__file__).parents[1]
load_dotenv(basedir / ".env")
# --- IMPORTS DE TES SERVICES ---
# Assure-toi que le fichier security.py est bien dans app/middleware/
from app.core.security import verify_security, increment_usage_async
from app.services.rag import add_knowledge_to_db, search_knowledge_base, save_conversation, get_all_conversations
from app.services.scraper import scrape_website



app = FastAPI(title="AI Support Bot API (Multi-Tenant)")

# --- SÉCURITÉ CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Configuration OpenAI
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

# --- MODÈLES DE DONNÉES ---
class ChatRequest(BaseModel):
    question: str
    context_url: str = None

class LearnRequest(BaseModel):
    text: str

class ScrapeRequest(BaseModel):
    url: str

# --- ROUTES ---

@app.get("/")
def read_root():
    return {"status": "online", "mode": "multi-tenant secured"}

@app.get("/api/history")
def history_endpoint(client_data: dict = Depends(verify_security)):
    """
    Permet au dashboard de récupérer la liste des discussions du client connecté.
    """
    try:
        # On passe l'ID du client sécurisé par le token
        return get_all_conversations(client_id=client_data['id'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learn")
def learn_endpoint(
    request: LearnRequest, 
    client_data: dict = Depends(verify_security) # <--- SÉCURISÉ
):
    try:
        # On passe le client_id pour que la donnée lui appartienne
        add_knowledge_to_db(request.text, client_id=client_data['id'])
        return {"message": "Information apprise avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
def scrape_endpoint(
    request: ScrapeRequest,
    client_data: dict = Depends(verify_security) # <--- SÉCURISÉ
):
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
        
        # On sauvegarde chaque chunk avec le client_id
        for i, chunk in enumerate(chunks):
            source_info = f"{request.url} (Partie {i+1}/{len(chunks)})"
            add_knowledge_to_db(chunk, client_id=client_data['id'], source=source_info)
        
        return {"message": f"Succès ! {len(chunks)} morceaux ajoutés pour {client_data['name']}."}
    except Exception as e:
        print(f"Erreur Scrape : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(
    request: ChatRequest,
    client_data: dict = Depends(verify_security) # <--- LE VIGILE
):
    try:
        client_id = client_data['id']
        
        # 1. RECHERCHE ISOLÉE (On ne cherche que dans les docs du client)
        context_results = search_knowledge_base(request.question, client_id=client_id)
        
        context_text = "\n\n".join(context_results)
        if not context_text: 
            context_text = "Aucune information spécifique trouvée dans la base."

        # 2. PROMPT PERSONNALISÉ
        system_prompt = f"""Tu es l'assistant de {client_data['name']}.
        Utilise UNIQUEMENT le contexte ci-dessous pour répondre.
        CONTEXTE: {context_text}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.question)
        ]
        
        # 3. GENERATION
        response = llm.invoke(messages)
        
        # 4. SAUVEGARDE & QUOTA
        # Incrémentation du quota en arrière-plan (non bloquant)
        await increment_usage_async(client_id)
        
        # Sauvegarde de la conversation (Idéalement ajouter client_id dans save_conversation plus tard)
        save_conversation(request.question, response.content, client_id=client_id)
        
        return {
            "response": response.content,
            "sources": context_results
        }

    except Exception as e:
        print(f"Erreur Chat : {e}")
        raise HTTPException(status_code=500, detail=str(e))