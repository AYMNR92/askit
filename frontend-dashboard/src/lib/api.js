// src/lib/api.js
const API_URL = import.meta.env.VITE_API_URL;
const TOKEN = import.meta.env.VITE_WIDGET_TOKEN;

export const api = {
  // Fonction générique pour faire des requêtes
  request: async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      'X-Widget-Token': TOKEN, // <--- Notre Header de sécurité
      ...options.headers,
    };

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(`${API_URL}${endpoint}`, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erreur ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("API Error:", error);
      throw error;
    }
  },

  // Raccourcis
  get: (endpoint) => api.request(endpoint, { method: 'GET' }),
  post: (endpoint, body) => api.request(endpoint, { method: 'POST', body: JSON.stringify(body) }),
};