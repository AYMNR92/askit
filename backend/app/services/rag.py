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

def add_knowledge_to_db(text: str, source: str = "manuel"):
    """
    Apprend un nouveau texte : le transforme en vecteur et le stocke dans Supabase.
    """
    # A. Transformer le texte en nombres (vecteur)
    vector = embeddings.embed_query(text)
    
    # B. Préparer les données
    data = {
        "content": text,
        "metadata": {"source": source},
        "embedding": vector
    }
    
    # C. Insérer dans Supabase
    response = supabase.table("documents").insert(data).execute()
    return response

def search_knowledge_base(query: str):
    """
    Cherche le texte le plus pertinent dans la base pour répondre à une question.
    """
    # A. Transformer la question en vecteur
    query_vector = embeddings.embed_query(query)
    
    # B. Appeler la fonction de recherche (celle qu'on a créée en SQL)
    params = {
        "query_embedding": query_vector,
        "match_threshold": 0.5, # Seuil de similarité (70%)
        "match_count": 3        # Récupérer les 3 meilleurs morceaux
    }
    
    response = supabase.rpc("match_documents", params).execute()
    
    # C. Retourner juste le texte
    return [doc['content'] for doc in response.data]

def save_conversation(user_question: str, bot_response: str):
    """
    Sauvegarde un échange dans la table 'conversations'.
    """
    data = {
        "messages": [
            {"role": "user", "content": user_question},
            {"role": "bot", "content": bot_response}
        ]
        # user_email reste null pour l'instant
    }
    supabase.table("conversations").insert(data).execute()

def get_all_conversations():
    """
    Récupère l'historique pour le dashboard, du plus récent au plus vieux.
    """
    response = supabase.table("conversations").select("*").order("created_at", desc=True).execute()
    return response.data