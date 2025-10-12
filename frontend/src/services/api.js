// src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Configuração base para fetch
const defaultOptions = {
  credentials: 'include', // Inclui cookies de autenticação
  headers: {
    'Content-Type': 'application/json',
  },
};

// Função auxiliar para fazer requisições
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || data.message || 'Erro na requisição');
    }

    return data;
  } catch (error) {
    console.error(`Erro na API ${endpoint}:`, error);
    throw error;
  }
}

// API de Topics
export const topicsAPI = {
  // Buscar tópicos do usuário
  getUserTopics: () => apiRequest('/topics/list'),

  // Buscar tópicos (autocomplete)
  searchTopics: (query, limit = 10) =>
    apiRequest(`/topics/search?q=${encodeURIComponent(query)}&limit=${limit}`),
};

// API de News
export const newsAPI = {
  // Buscar notícias do usuário (feed principal)
  getUserNews: (page = 1, perPage = 10) =>
    apiRequest(`/news/?page=${page}&per_page=${perPage}`),

  // Buscar notícias por tópico
  getNewsByTopic: (topicId, page = 1, perPage = 10) =>
    apiRequest(`/news/topic/${topicId}?page=${page}&per_page=${perPage}`),

  // Buscar notícia específica por ID
  getNewsById: (newsId) => apiRequest(`/news/${newsId}`),

  // Favoritar notícia
  favoriteNews: (newsId) =>
    apiRequest(`/news/${newsId}/favorite`, { method: 'POST' }),

  // Desfavoritar notícia
  unfavoriteNews: (newsId) =>
    apiRequest(`/news/${newsId}/favorite`, { method: 'PUT' }),
};

// API de Users
export const usersAPI = {
  // Buscar perfil do usuário
  getUserProfile: () => apiRequest('/users/profile'),
};