import os
import pathlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from fastapi.middleware.cors import CORSMiddleware # <--- INDISPENSABLE

# Import des fonctions de mémoire (Supabase)
from app.services.rag import add_knowledge_to_db, search_knowledge_base, save_conversation, get_all_conversations
from app.services.scraper import scrape_website
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration des chemins (.env)
basedir = pathlib.Path(__file__).parents[1]
load_dotenv(basedir / ".env")

app = FastAPI(title="AI Support Bot API")

# --- LE BLOC DE SÉCURITÉ (CORS) ---
# C'est ce bloc qui manquait ou qui était mal configuré
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise tout le monde (localhost:5173, localhost:3000, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)
# ----------------------------------

# Configuration OpenAI
api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

# Modèles de données
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
    return {"status": "online"}

@app.get("/api/history")
def history_endpoint():
    """
    Permet au dashboard de récupérer la liste des discussions.
    """
    try:
        return get_all_conversations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learn")
def learn_endpoint(request: LearnRequest):
    try:
        add_knowledge_to_db(request.text)
        return {"message": "Information apprise avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
def scrape_endpoint(request: ScrapeRequest):
    """
    Aspire une page, la découpe en morceaux et l'apprend.
    """
    try:
        print(f"1. Aspiration de : {request.url}")
        # On utilise ta fonction scraper qui n'a PLUS de limite [:4000]
        raw_text = scrape_website(request.url)
        
        if not raw_text:
            raise HTTPException(status_code=400, detail="Page vide.")

        # 2. DÉCOUPAGE (CHUNKING) PRO
        # On coupe en blocs de 1000 caractères (environ 10-15 phrases)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(raw_text)
        
        print(f"2. Texte découpé en {len(chunks)} morceaux.")

        # 3. SAUVEGARDE
        for i, chunk in enumerate(chunks):
            source_info = f"{request.url} (Partie {i+1}/{len(chunks)})"
            add_knowledge_to_db(chunk, source=source_info)
        
        return {
            "message": f"Succès ! {len(chunks)} morceaux de savoir ajoutés.", 
            "preview": f"Page découpée et apprise via {len(chunks)} entrées."
        }
        
    except Exception as e:
        print(f"Erreur Scrape : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        # 1. RECHERCHE : On demande à Supabase les infos pertinentes
        context_results = search_knowledge_base(request.question)
        
        # On colle les morceaux de textes trouvés ensemble
        context_text = "\n\n".join(context_results)
        
        if not context_text:
            context_text = "Aucune information spécifique trouvée dans la base."

        # 2. PROMPT : On donne les consignes à l'IA avec le contexte
        system_prompt = f"""Tu es un assistant service client pour une boutique en ligne.
        
        RÈGLES IMPORTANTES :
        1. Utilise UNIQUEMENT le contexte ci-dessous pour répondre.
        2. Si la réponse n'est pas dans le contexte, dis poliment que tu ne sais pas.
        3. Sois concis et professionnel.

        CONTEXTE TROUVÉ DANS LA BASE DE DONNÉES :
        {context_text}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.question)
        ]
        
        # 3. GÉNÉRATION
        response = llm.invoke(messages)
        
        # 4. SAUVEGARDE DE LA CONVERSATION
        save_conversation(request.question, response.content)
        
        return {
            "response": response.content,
            "sources": context_results
        }

    except Exception as e:
        print(f"Erreur : {e}")
        raise HTTPException(status_code=500, detail=str(e))