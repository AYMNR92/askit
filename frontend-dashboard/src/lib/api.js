const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = {
  request: async (endpoint, options = {}) => {
    // 1. On récupère le token stocké lors de la connexion
    const token = localStorage.getItem('access_token');
    
    const headers = {
      'Content-Type': 'application/json',
      // 2. Si un token existe, on l'ajoute (C'est le sésame pour le Backend)
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    };

    const config = { ...options, headers };

    try {
      const response = await fetch(`${API_URL}${endpoint}`, config);
      
      // 3. Si le token est expiré (401), on déconnecte l'utilisateur
      if (response.status === 401) {
        localStorage.removeItem('access_token');
        // Redirection forcée vers le login (sauf si on y est déjà)
        if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
        }
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erreur ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      throw error;
    }
  },

  get: (endpoint) => api.request(endpoint, { method: 'GET' }),
  post: (endpoint, body) => api.request(endpoint, { method: 'POST', body: JSON.stringify(body) }),
  // Pour les formulaires (ex: login)
  postForm: (endpoint, body) => api.request(endpoint, { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body 
  }),
};