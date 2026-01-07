import requests
from bs4 import BeautifulSoup

def scrape_website(url: str) -> str:
    """
    Télécharge une page web et extrait tout le texte visible.
    """
    try:
        # 1. Se faire passer pour un navigateur (sinon certains sites bloquent)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 2. Télécharger la page
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Vérifie qu'il n'y a pas d'erreur 404/500
        
        # 3. Analyser le HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 4. Nettoyage : On vire les scripts JS et le CSS
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        # 5. Récupérer le texte
        text = soup.get_text(separator=' ')
        
        # 6. Nettoyer les espaces vides inutiles
        lines = (line.strip() for line in text.splitlines())
        clean_text = '\n'.join(chunk for chunk in lines if chunk)
        
        return clean_text[:4000] # On limite à 4000 caractères pour ne pas exploser la base pour l'instant

    except Exception as e:
        raise ValueError(f"Impossible de lire l'URL : {str(e)}")