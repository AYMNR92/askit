import { useState } from 'preact/hooks';
import './index.css';

export function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Bonjour ! Comment puis-je vous aider ?' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    // 1. Ajouter le message de l'utilisateur à la liste
    const userMsg = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      // 2. Envoyer au Backend
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg.content })
      });

      const data = await response.json();

      // 3. Ajouter la réponse du bot
      const botMsg = { role: 'bot', content: data.response };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("Erreur:", error);
      setMessages((prev) => [...prev, { role: 'bot', content: "Oups, j'ai eu un problème de connexion..." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Bouton pour ouvrir */}
      <button className="chat-bubble-btn" onClick={toggleChat}>
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Fenêtre de chat */}
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">Support Client</div>
          
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
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>
      )}
    </>
  );
}