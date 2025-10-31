// src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Configuração base para fetch
const defaultOptions = {
  credentials: "include", // Inclui cookies de autenticação
  headers: {
    "Content-Type": "application/json",
  },
};

// Função auxiliar para ler um cookie pelo nome
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

// Função auxiliar para fazer requisições
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const method = options.method || "GET";

  // Adiciona o token CSRF automaticamente para métodos que alteram dados
  const csrfMethods = ["POST", "PUT", "DELETE", "PATCH"];
  if (csrfMethods.includes(method.toUpperCase())) {
    const csrfToken = getCookie("csrf_access_token");
    if (csrfToken) {
      defaultOptions.headers["X-CSRF-TOKEN"] = csrfToken;
    }
  }

  const config = {
    ...defaultOptions,
    ...options,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || data.message || "Request error");
    }

    return data;
  } catch (error) {
    console.error(`Erro na API ${endpoint}:`, error);
    throw error;
  }
}

// API de Topics
export const topicsAPI = {
  // --- Tópicos Padrão ---
  // Lista todos os tópicos padrão do sistema
  getStandardTopics: () => apiRequest("/topics/standard"),

  // --- Tópicos Customizados (Preferências do Usuário) ---
  // Lista os tópicos preferidos do usuário
  getPreferredTopics: () => apiRequest("/topics/custom"),
  addPreferredTopic: (name) =>
    apiRequest("/topics/custom", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  // Remove um tópico das preferências do usuário
  removePreferredTopic: (topicId) =>
    apiRequest(`/topics/custom/${topicId}`, { method: "DELETE" }),
};

// API de News
export const newsAPI = {
  // Buscar notícias do usuário (feed principal)
  getUserNews: (page = 1, perPage = 10) =>
    apiRequest(`/news/?page=${page}&per_page=${perPage}`),

  // Buscar feed personalizado "For You" (com ranking baseado em preferências)
  getForYouNews: (page = 1, perPage = 10) =>
    apiRequest(`/news/for-you?page=${page}&per_page=${perPage}`),

  // Buscar notícias por tópico
  getNewsByTopic: (topicId, page = 1, perPage = 10) =>
    apiRequest(`/news/topic/${topicId}?page=${page}&per_page=${perPage}`),

  // Buscar notícia específica por ID
  getNewsById: (newsId) => apiRequest(`/news/${newsId}`),

  // Favoritar notícia
  favoriteNews: (newsId) =>
    apiRequest(`/news/${newsId}/favorite`, { method: "POST" }),

  // Desfavoritar notícia
  unfavoriteNews: (newsId) =>
    apiRequest(`/news/${newsId}/favorite`, { method: "PUT" }),

  // Busca as noticias favoritas por usuario
  getSavedNews: () => apiRequest(`/news/saved`, { method: "GET" }),

  // Adiciona uma notícia ao histórico de leitura do usuário
  addNewsToHistory: (newsId) =>
    apiRequest(`/news/${newsId}/history`, { method: "POST" }),

  // Busca o histórico de notícias lidas pelo usuário
  getHistory: async (page = 1, perPage = 50) => {
    return apiRequest(`/news/history?page=${page}&per_page=${perPage}`);
  },
};

// API de Users
export const usersAPI = {
  // Buscar perfil do usuário
  getUserProfile: () => apiRequest("/users/profile"),
};

// API de News Sources
export const newsSourcesAPI = {
  // Lista todas as fontes disponíveis no sistema
  getAllSources: () => apiRequest("/news_sources/list_all"),

  // Lista as fontes que o usuário marcou como preferidas
  getAttachedSources: () =>
    apiRequest("/news_sources/list_all_attached_sources"),

  // Associa uma fonte ao usuário
  attachSource: (sourceId) =>
    apiRequest("/news_sources/attach", {
      method: "POST",
      body: JSON.stringify({ source_id: sourceId }),
    }),

  // Desassocia uma fonte do usuário
  detachSource: (sourceId) =>
    apiRequest(`/news_sources/detach/${sourceId}`, { method: "DELETE" }),
};
