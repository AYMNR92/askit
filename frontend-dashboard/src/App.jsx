import { useState, useEffect } from 'react';
import { 
  BookOpen, 
  MessageSquare, 
  LayoutDashboard, 
  Save, 
  CheckCircle, 
  Loader2, 
  GraduationCap, 
  ArrowRight 
} from 'lucide-react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('history'); 
  const [history, setHistory] = useState([]);
  const [textToLearn, setTextToLearn] = useState('');
  const [status, setStatus] = useState(null); // 'idle', 'loading', 'success', 'error'

  // --- 1. CHARGEMENT DE L'HISTORIQUE ---
  const fetchHistory = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/history');
      const data = await res.json();
      setHistory(data);
    } catch (e) {
      console.error("Erreur fetch history:", e);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') fetchHistory();
  }, [activeTab]);

  // --- 2. APPRENTISSAGE ---
  const handleLearn = async () => {
    if (!textToLearn.trim()) return;
    setStatus('loading');
    
    try {
      await fetch('http://127.0.0.1:8000/api/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToLearn }),
      });
      setStatus('success');
      setTextToLearn('');
      // Petit délai pour l'animation de succès
      setTimeout(() => setStatus(null), 3000);
    } catch (e) {
      console.error(e);
      setStatus('error');
    }
  };

  // --- 3. FONCTION "EN FAIRE UNE RÈGLE" ---
  const sendToLearning = (userQuestion) => {
    setTextToLearn(`Question : "${userQuestion}" \nRéponse à apprendre : `);
    setActiveTab('teach');
  };

  return (
    <div className="dashboard-container">
      
      {/* --- HEADER --- */}
      <header className="header">
        <h1>
          <LayoutDashboard size={28} className="text-primary" /> 
          AI Admin Panel
        </h1>
        <span className="badge">v1.0 Live</span>
      </header>

      {/* --- NAVIGATION --- */}
      <nav className="tabs">
        <button 
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <MessageSquare size={18} /> Conversations
        </button>
        <button 
          className={`tab-btn ${activeTab === 'teach' ? 'active' : ''}`}
          onClick={() => setActiveTab('teach')}
        >
          <BookOpen size={18} /> Base de connaissances
        </button>
      </nav>

      {/* --- CONTENU : BASE DE CONNAISSANCES --- */}
      {activeTab === 'teach' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
          
          {/* CARTE 1 : Manuel */}
          <div className="card learning-area animate-fade-in">
            <h2>✍️ Ajouter du texte manuellement</h2>
            <span className="subtitle">Copiez-collez ici vos règles, FAQ ou procédures.</span>
            <textarea
              value={textToLearn}
              onChange={(e) => setTextToLearn(e.target.value)}
              placeholder="Ex: Si le client demande les délais, répondre que c'est 24h..."
            />
            <div className="action-row">
              <button className="btn-primary" onClick={handleLearn} disabled={status === 'loading'}>
                {status === 'loading' ? <Loader2 size={18} className="spin"/> : <Save size={18} />}
                Enregistrer le texte
              </button>
              {status === 'success' && <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>Sauvegardé !</span>}
            </div>
          </div>

          {/* CARTE 2 : Scraper URL (NOUVEAU) */}
          <div className="card learning-area animate-fade-in" style={{ borderLeft: '4px solid #8b5cf6' }}>
            <h2>🌐 Aspirer une page web</h2>
            <span className="subtitle">Entrez l'URL d'une page publique (FAQ, Blog, Produit) pour l'apprendre automatiquement.</span>
            
            <div style={{ display: 'flex', gap: '10px' }}>
              <input 
                type="url" 
                id="urlInput"
                placeholder="https://mon-site.com/faq"
                style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ccc' }}
              />
              <button 
                className="btn-primary" 
                style={{ background: '#8b5cf6' }} // Violet pour distinguer
                onClick={async (e) => {
                  const url = document.getElementById('urlInput').value;
                  if(!url) return;
                  const btn = e.target;
                  const originalText = btn.innerText;
                  btn.innerText = "Aspiration...";
                  btn.disabled = true;

                  try {
                    const res = await fetch('http://127.0.0.1:8000/api/scrape', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/json'},
                      body: JSON.stringify({ url: url })
                    });
                    if(res.ok) {
                      alert("Page apprise avec succès !");
                      document.getElementById('urlInput').value = "";
                    } else {
                      alert("Erreur lors de l'aspiration.");
                    }
                  } catch(err) { console.error(err); }
                  
                  btn.innerText = originalText;
                  btn.disabled = false;
                }}
              >
                Scanner l'URL
              </button>
            </div>
          </div>

        </div>
      )}

      {/* --- CONTENU : HISTORIQUE --- */}
      {activeTab === 'history' && (
        <div className="conversations-list animate-fade-in">
          {history.length === 0 && (
            <div className="empty-state">Aucune conversation enregistrée pour le moment.</div>
          )}

          {history.map((conv) => (
            <div key={conv.id} className="conv-card">
              <div className="conv-header">
                <span>📅 {new Date(conv.created_at).toLocaleString()}</span>
                <span>ID: {conv.id.slice(0, 8)}...</span>
              </div>
              
              <div className="conv-body">
                {conv.messages.map((msg, idx) => (
                  <div key={idx} className={`msg-row ${msg.role}`}>
                    
                    <div className={`bubble ${msg.role}`}>
                      {msg.content}
                    </div>

                    {/* Bouton pour enseigner si c'est une question client */}
                    {msg.role === 'user' && (
                      <button 
                        className="teach-link"
                        onClick={() => sendToLearning(msg.content)}
                        title="Créer une réponse automatique"
                      >
                        <GraduationCap size={14} /> Enseigner à l'IA <ArrowRight size={12}/>
                      </button>
                    )}

                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}

export default App;