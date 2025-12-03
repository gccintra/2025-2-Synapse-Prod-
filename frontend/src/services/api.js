const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const defaultOptions = {
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
  },
};

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const config = {
    ...defaultOptions,
    ...options,
  };
  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      // Diferencia erro 401 (não autorizado) de outros erros
      if (response.status === 401) {
        const authError = new Error(data.error || data.message || "Authentication required");
        authError.status = 401;
        authError.isAuthError = true;
        throw authError;
      }

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
  // Lista todos os tópicos padrão
  getStandardTopics: () => apiRequest("/topics/standard"),

  // Lista os tópicos preferidos
  getPreferredTopics: () => apiRequest("/topics/custom"),
  addPreferredTopic: (name) =>
    apiRequest("/topics/custom", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),

  // Remove um tópico das preferências
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
  // Buscar perfil
  getUserProfile: () => apiRequest("/users/profile"),

  // Atualizar perfil
  updateUserProfile: (userData) =>
    apiRequest("/users/profile/update", {
      method: "PUT",
      body: JSON.stringify(userData),
    }),

  // Mudar a senha
  changePassword: (passwordData) =>
    apiRequest("/users/profile/change_password", {
      method: "PUT",
      body: JSON.stringify(passwordData),
    }),

  changeNewsletter: (value) =>
    apiRequest("/users/profile/newsletter", {
      method: "PUT",
      body: JSON.stringify({ value }),
    }),

  // Fazer logout
  logout: () => apiRequest("/users/logout", { method: "POST" }),
};

// News Sources
export const newsSourcesAPI = {
  getAllSources: () => apiRequest("/news_sources/list_all"),

  getAttachedSources: () =>
    apiRequest("/news_sources/list_all_attached_sources"),

  attachSource: (sourceId) =>
    apiRequest("/news_sources/attach", {
      method: "POST",
      body: JSON.stringify({ source_id: sourceId }),
    }),

  detachSource: (sourceId) =>
    apiRequest(`/news_sources/detach/${sourceId}`, { method: "DELETE" }),

  getUnattachedSources: () =>
    apiRequest("/news_sources/list_all_unattached_sources"),
};
