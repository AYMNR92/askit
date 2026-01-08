import os
import pathlib
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_openai import OpenAIEmbeddings

basedir = pathlib.Path(__file__).parents[2]
load_dotenv(basedir / ".env")

# 1. Connexion à Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
api_key = os.getenv("OPENAI_API_KEY")

if not url or not key:
    raise ValueError("⚠️ Supabase URL ou KEY manquante dans le .env")

supabase: Client = create_client(url, key)
# 2. Initialisation de l'outil qui transforme le texte en vecteurs (Embeddings)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)

def add_knowledge_to_db(text: str, client_id: str, source: str = "manuel"):
    """
    Apprend un texte POUR UN CLIENT SPÉCIFIQUE.
    """
    vector = embeddings.embed_query(text)
    
    data = {
        "content": text,
        "metadata": {"source": source},
        "embedding": vector,
        "client_id": client_id  # <--- AJOUT CRITIQUE
    }
    
    response = supabase.table("documents").insert(data).execute()
    return response

def search_knowledge_base(query: str, client_id: str):
    """
    Cherche uniquement dans les données du client_id.
    """
    query_vector = embeddings.embed_query(query)
    
    params = {
        "query_embedding": query_vector,
        "match_threshold": 0.5,
        "match_count": 3,
        "filter_client_id": client_id # <--- LE FILTRE DE SÉCURITÉ
    }
    
    response = supabase.rpc("match_documents", params).execute()
    return [doc['content'] for doc in response.data]

def save_conversation(user_question: str, bot_response: str, client_id: str = None):
    data = {
        "messages": [
            {"role": "user", "content": user_question},
            {"role": "bot", "content": bot_response}
        ]
    }
    # Si tu as ajouté la colonne client_id dans 'conversations' (recommandé)
    if client_id:
        data["client_id"] = client_id
        
    supabase.table("conversations").insert(data).execute()

def get_all_conversations(client_id: str):
    """
    Récupère l'historique UNIQUEMENT pour le client connecté.
    """
    response = supabase.table("conversations")\
        .select("*")\
        .eq("client_id", client_id)\
        .order("created_at", desc=True)\
        .execute()
    return response.data