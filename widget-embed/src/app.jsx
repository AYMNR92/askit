import { useState, useMemo } from 'preact/hooks';
import './index.css';

// --- 1. FONCTION UTILITAIRE POUR RÉCUPÉRER LA CONFIG ---
const getWidgetConfig = () => {
  // On cherche la balise <script> qui possède l'attribut 'data-token'
  // Cela permet de récupérer la config que le client a collée sur son site
  const script = document.querySelector('script[data-token]');
  
  if (script) {
    return {
      token: script.getAttribute('data-token'),
      // Si pas de couleur définie, on met du bleu par défaut
      primaryColor: script.getAttribute('data-color') || '#2563eb' 
    };
  }
  
  // Valeurs par défaut (utile pour tes tests en local si tu n'as pas le script)
  console.warn("Widget: Aucun token trouvé dans le script !");
  return { token: null, primaryColor: '#2563eb' };
};

export function App() {
  // On charge la config une seule fois au démarrage
  const config = useMemo(() => getWidgetConfig(), []);

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Bonjour ! Comment puis-je vous aider ?' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const toggleChat = () => setIsOpen(!isOpen);
   
  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    // Vérification de sécurité basique
    if (!config.token) {
        alert("Erreur de configuration : Token manquant.");
        return;
    }

    const userMsg = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      // --- 2. ENVOI SÉCURISÉ AU BACKEND ---
      const response = await fetch('https://askit-9u2q.onrender.com/api/chat', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-Widget-Token': config.token // <--- C'EST ICI QUE LA MAGIE OPÈRE 🛡️
        },
        body: JSON.stringify({ question: userMsg.content })
      });

      // Gestion des erreurs spécifiques (403, 429, etc.)
      if (!response.ok) {
        if (response.status === 403) throw new Error("Domaine non autorisé.");
        if (response.status === 429) throw new Error("Trop de demandes, réessayez plus tard.");
        if (response.status === 402) throw new Error("Quota dépassé.");
        throw new Error("Erreur serveur");
      }

      const data = await response.json();

      const botMsg = { role: 'bot', content: data.response };
      setMessages((prev) => [...prev, botMsg]);

    } catch (error) {
      console.error("Erreur:", error);
      // On affiche l'erreur spécifique à l'utilisateur (optionnel, mais utile pour le debug)
      let errorMsg = "Oups, j'ai eu un problème de connexion...";
      if (error.message.includes("Domaine")) errorMsg = "⚠️ Widget non autorisé sur ce site.";
      if (error.message.includes("Trop de demandes")) errorMsg = "⚠️ Vous parlez trop vite !";
      
      setMessages((prev) => [...prev, { role: 'bot', content: errorMsg }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Bouton pour ouvrir - Couleur dynamique */}
      <button 
        className="chat-bubble-btn" 
        onClick={toggleChat}
        style={{ backgroundColor: config.primaryColor }} 
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Fenêtre de chat */}
      {isOpen && (
        <div className="chat-window">
          {/* Header - Couleur dynamique */}
          <div 
            className="chat-header"
            style={{ backgroundColor: config.primaryColor }}
          >
            Support Client
          </div>
           
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {isLoading && <div className="message bot">...</div>}
          </div>

          <div className="chat-input-area">
            <input 
              type="text" 
              placeholder="Posez votre question..." 
              value={inputValue}
              onInput={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            {/* Bouton d'envoi - Couleur texte dynamique */}
            <button 
                onClick={sendMessage}
                style={{ color: config.primaryColor }}
            >
                ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}