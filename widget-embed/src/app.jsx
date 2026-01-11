import { useState, useEffect, useRef, useMemo } from 'preact/hooks';
import './index.css'; // Assure-toi que c'est bien index.css qui contient @tailwind

const getWidgetConfig = () => {
  // On cherche le script qui contient l'attribut data-token
  const script = document.currentScript || document.querySelector('script[data-token]');
  
  return {
    // Si on trouve l'attribut, on l'utilise. Sinon, on met une chaine vide (et ça fera une erreur normale)
    token: script?.getAttribute('data-token') || "", 
    primaryColor: script?.getAttribute('data-color') || "#2563eb"
  };
};

// --- ICONES SVG SIMPLES (Pas besoin de librairie) ---
const Icons = {
  MessageCircle: () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>,
  X: () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>,
  Send: () => <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>,
  Bot: () => <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
};

export function App() {
  const config = useMemo(() => getWidgetConfig(), []);
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Bonjour ! Comment puis-je vous aider ?' }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // Auto-scroll
  const messagesEndRef = useRef(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, isOpen]);

  const sendMessage = async (e) => {
    if(e) e.preventDefault();
    if (!inputValue.trim()) return;

    const userMsg = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch('https://askit-9u2q.onrender.com/api/chat', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-Widget-Token': config.token
        },
        body: JSON.stringify({ 
            question: userMsg.content,
            history: messages
        })
      });

      if (!response.ok) throw new Error("Erreur serveur");
      const data = await response.json();
      
      const botResponse = data.response || data.message || "Désolé, je n'ai pas compris.";
      setMessages((prev) => [...prev, { role: 'bot', content: botResponse }]);

    } catch (error) {
      console.error("Widget Error:", error);
      setMessages((prev) => [...prev, { role: 'bot', content: "Oups, je rencontre un problème technique." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-[99999] font-sans antialiased">
      
      {/* FENÊTRE DE CHAT */}
      {isOpen && (
        <div className="absolute bottom-20 right-0 w-[350px] bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-100 animate-enter flex flex-col h-[500px]">
          
          {/* HEADER */}
          <div 
            className="p-4 flex items-center gap-3 text-white shadow-sm"
            style={{ backgroundColor: config.primaryColor }}
          >
            <div className="p-2 bg-white/20 rounded-full">
              <Icons.Bot />
            </div>
            <div>
              <h3 className="font-semibold text-sm">Assistant Virtuel</h3>
              <p className="text-[11px] opacity-90">Répond instantanément</p>
            </div>
            <button 
                onClick={() => setIsOpen(false)} 
                className="ml-auto hover:bg-white/20 p-1.5 rounded-full transition-colors"
            >
              <Icons.X />
            </button>
          </div>

          {/* ZONE MESSAGES */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === 'bot' && (
                    <div className="w-6 h-6 rounded-full flex items-center justify-center mr-2 mt-1 shrink-0" style={{ backgroundColor: config.primaryColor + '20' }}>
                        <span className="text-[10px] font-bold" style={{ color: config.primaryColor }}>IA</span>
                    </div>
                )}

                <div
                  className={`max-w-[80%] p-3 text-sm shadow-sm ${
                    msg.role === "user"
                      ? "text-white rounded-2xl rounded-br-none"
                      : "bg-white border border-gray-100 text-slate-800 rounded-2xl rounded-bl-none"
                  }`}
                  style={msg.role === "user" ? { backgroundColor: config.primaryColor } : {}}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start items-center gap-2">
                 <div className="w-6 h-6 shrink-0" />
                 <div className="bg-white border border-gray-100 px-3 py-2 rounded-2xl rounded-bl-none shadow-sm flex gap-1">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                 </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* INPUT AREA */}
          <div className="p-3 bg-white border-t border-gray-100">
            <div className="flex items-center gap-2 bg-gray-50 p-1.5 rounded-full border border-gray-200 focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-300 transition-all">
              <input
                value={inputValue}
                onInput={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage(e)}
                placeholder="Posez votre question..."
                className="flex-1 px-3 bg-transparent text-sm focus:outline-none min-w-0"
              />
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim()}
                className="w-8 h-8 rounded-full flex items-center justify-center text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 shrink-0"
                style={{ backgroundColor: config.primaryColor }}
              >
                <Icons.Send />
              </button>
            </div>
            
            {/* Branding Discret */}
            <div className="mt-2 text-center">
                <p className="text-[10px] text-gray-400">
                    Propulsé par <span className="font-medium text-gray-500">Askit AI</span>
                </p>
            </div>
          </div>
        </div>
      )}

      {/* BOUTON FLOTTANT (FAB) */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-14 h-14 rounded-full flex items-center justify-center text-white shadow-lg transition-transform hover:scale-110 active:scale-95"
        style={{
          backgroundColor: config.primaryColor,
          boxShadow: `0 4px 14px ${config.primaryColor}66`,
        }}
      >
        {isOpen ? <Icons.X /> : <Icons.MessageCircle />}
      </button>

    </div>
  );
}