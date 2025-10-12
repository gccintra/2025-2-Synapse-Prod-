import React, { useState, useEffect } from "react";
import HeaderFeedPage from "../components/FeedPage/HeaderFeedPage";
import NewsCard from "../components/FeedPage/NewsCard";
import { topicsAPI, usersAPI, newsAPI } from "../services/api";
import { useInfiniteScroll } from "../hooks/useInfiniteScroll";


const FeedPage = () => {
  const [userData, setUserData] = useState({ email: "" });
  const [initialLoading, setInitialLoading] = useState(true);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null); // null = "For You"
  const [topicsLoading, setTopicsLoading] = useState(true);

  // Função para buscar notícias baseada no filtro selecionado
  const fetchNews = (page, perPage) => {
    if (selectedTopic) {
      return newsAPI.getNewsByTopic(selectedTopic.id, page, perPage);
    } else {
      return newsAPI.getUserNews(page, perPage);
    }
  };

  // Hook de infinite scroll
  const {
    data: news,
    loading: newsLoading,
    hasMore,
    error: newsError,
    lastElementRef,
    reset: resetNews
  } = useInfiniteScroll(fetchNews, {
    dependencies: [selectedTopic], // Reset quando o tópico mudar
    perPage: 10
  });

  useEffect(() => {
    const fetchInitialData = async () => {
      setInitialLoading(true);
      setTopicsLoading(true);

      try {
        // Buscar dados do usuário e tópicos em paralelo
        const [userResponse, topicsResponse] = await Promise.allSettled([
          usersAPI.getUserProfile(),
          topicsAPI.getUserTopics()
        ]);

        // Processar dados do usuário
        if (userResponse.status === 'fulfilled') {
          setUserData(userResponse.value.data);
        } else {
          console.error("Failed to fetch user data:", userResponse.reason);
        }

        if (topicsResponse.status === 'fulfilled') {
          setTopics(topicsResponse.value.data || []);
        } else {
          console.error("Failed to fetch topics:", topicsResponse.reason);
        }
      } catch (err) {
        console.error("Connection error:", err);
      } finally {
        setInitialLoading(false);
        setTopicsLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* 1. Header do Feed */}
      <HeaderFeedPage userEmail={userData.email} />

      {/* Main Content Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {/* Filtros */}
        <div className="flex gap-4 mb-8 flex-wrap">
          {/* Botão "For You" */}
          <button
            onClick={() => setSelectedTopic(null)}
            className={`flex items-center gap-3 mt-6 text-gray-900 text-xs border border-black shadow-lg pl-6 pr-6 py-1 rounded-full font-montserrat transition-all duration-300 ease-in-out hover:scale-[1.01] hover:shadow-xl hover:-translate-y-0.5 cursor-pointer ${
              selectedTopic === null
                ? "bg-black text-white [font-weight:600]"
                : "bg-white hover:bg-gray-300 [font-weight:500]"
            }`}
          >
            For You
          </button>

          {/* Tópicos do usuário */}
          {topicsLoading ? (
            // Skeleton loading para filtros
            Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="mt-6 h-6 w-20 bg-gray-300 rounded-full animate-pulse"
              />
            ))
          ) : (
            topics.map((topic) => (
              <button
                key={topic.id}
                onClick={() => setSelectedTopic(topic)}
                className={`flex items-center gap-3 mt-6 text-gray-900 text-xs border border-black shadow-lg pl-6 pr-6 py-1 rounded-full font-montserrat transition-all duration-300 ease-in-out hover:scale-[1.01] hover:shadow-xl hover:-translate-y-0.5 cursor-pointer ${
                  selectedTopic?.id === topic.id
                    ? "bg-black text-white [font-weight:600]"
                    : "bg-white hover:bg-gray-300 [font-weight:500]"
                }`}
              >
                {topic.name}
              </button>
            ))
          )}
        </div>

        {/* Exibir erro se houver */}
        {newsError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p>Erro ao carregar notícias: {newsError}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-2 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Tentar novamente
            </button>
          </div>
        )}

        {/* Grid para os 3 primeiros cards (Destaques) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 mb-12">
          {(newsLoading && news.length === 0)
            ? // Renderiza 3 cards em estado de carregamento inicial
              Array.from({ length: 3 }).map((_, index) => (
                <NewsCard key={index} isLoading={true} />
              ))
            : news.slice(0, 3).map((newsItem) => (
                <NewsCard key={newsItem.id} news={newsItem} />
              ))}
        </div>

        {/* Layout em Lista para os demais (Corpo do Feed) */}
        <div className="space-y-0">
          {(newsLoading && news.length === 0)
            ? Array.from({ length: 2 }).map((_, index) => (
                <NewsCard key={index} isListItem={true} isLoading={true} />
              ))
            : news.slice(3).map((newsItem, index) => {
                // Adicionar ref ao último elemento para infinite scroll
                const isLastItem = index === news.slice(3).length - 1;
                return (
                  <NewsCard
                    key={newsItem.id}
                    news={newsItem}
                    isListItem={true}
                    ref={isLastItem ? lastElementRef : undefined}
                  />
                );
              })}
        </div>

        {/* Indicador de carregamento para infinite scroll */}
        {newsLoading && news.length > 0 && (
          <div className="flex justify-center py-8">
            <div className="space-y-4 w-full">
              {Array.from({ length: 2 }).map((_, index) => (
                <NewsCard key={`loading-${index}`} isListItem={true} isLoading={true} />
              ))}
            </div>
          </div>
        )}

        {/* Mensagem quando não há mais dados */}
        {!hasMore && news.length > 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>Não há mais notícias para exibir.</p>
          </div>
        )}

        {/* Mensagem quando não há dados */}
        {!newsLoading && news.length === 0 && !newsError && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">Nenhuma notícia encontrada.</p>
            {selectedTopic && (
              <p className="text-gray-400 mt-2">
                Tente selecionar outro tópico ou volte para "For You"
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default FeedPage;
