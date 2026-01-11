from passlib.context import CryptContext
from supabase import create_client
import os
import secrets
from dotenv import load_dotenv

# Charger les variables
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Erreur: .env mal configuré")
    exit(1)

supabase = create_client(url, key)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- TES INFOS ---
EMAIL = "admin@askit.com"
PASSWORD = "ton_mot_de_passe_secret"
# -----------------

print(f"🔍 Recherche de l'utilisateur {EMAIL}...")

# 1. On récupère l'ID de l'utilisateur existant
existing_user = supabase.table("clients").select("id").eq("email", EMAIL).execute()

if existing_user.data:
    user_id = existing_user.data[0]['id']
    print(f"🔄 Utilisateur trouvé (ID: {user_id}). Nettoyage en cours...")

    # 2. ON SUPPRIME LES DÉPENDANCES D'ABORD (Enfants)
    try:
        # Supprime les documents liés
        supabase.table("documents").delete().eq("client_id", user_id).execute()
        print("✅ Documents nettoyés.")
    except Exception as e:
        print(f"Info Docs: {e}")

    try:
        # Supprime les conversations liées (au cas où)
        supabase.table("conversations").delete().eq("client_id", user_id).execute()
        print("✅ Conversations nettoyées.")
    except Exception as e:
        print(f"Info Convs: {e}")
        
    try:
        # Supprime les logs de sécurité (au cas où)
        supabase.table("security_logs").delete().eq("client_id", user_id).execute()
        print("✅ Logs nettoyés.")
    except Exception as e:
        pass

    # 3. ON SUPPRIME LE PARENT
    try:
        supabase.table("clients").delete().eq("id", user_id).execute()
        print("🗑️  Ancien utilisateur supprimé.")
    except Exception as e:
        print(f"❌ Erreur critique lors de la suppression du client : {e}")
        exit(1)

else:
    print("✨ Aucun utilisateur existant trouvé, on peut créer.")

print(f"🔐 Hachage du mot de passe...")
password_hash = pwd_context.hash(PASSWORD)

# Génération des tokens
public_token = f"pub_{secrets.token_hex(16)}"
secret_key = f"sk_{secrets.token_hex(24)}"

data = {
    "email": EMAIL,
    "name": "Super Admin",
    "password_hash": password_hash,
    "is_active": True,
    "public_token": public_token,
    "secret_key": secret_key
}

try:
    response = supabase.table("clients").insert(data).execute()
    print("\n✅ VICTOIRE ! Utilisateur admin recréé à neuf.")
    print("------------------------------------------------")
    print(f"📧 Login : {EMAIL}")
    print(f"🔑 Pass  : {PASSWORD}")
    print("------------------------------------------------")
except Exception as e:
    print(f"\n❌ Erreur : {e}")