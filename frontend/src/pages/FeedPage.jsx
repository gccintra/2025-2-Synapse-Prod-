import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import HeaderFeedPage from "../components/FeedPage/HeaderFeedPage";
import NewsCard from "../components/FeedPage/NewsCard";
import { topicsAPI, usersAPI, newsAPI } from "../services/api";
import { useInfiniteScroll } from "../hooks/useInfiniteScroll";

const LoginPrompt = () => (
  <div className="relative">
    {/* Overlay com blur e mensagem */}
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-lg bg-white/30 p-8 text-center backdrop-blur-md">
      <h2 className="text-2xl font-bold text-gray-900 font-montserrat">
        Access your personalized feed
      </h2>
      <p className="mt-2 text-gray-700 font-montserrat">
        Please log in to see the news tailored specifically for you.
      </p>
      <Link
        to="/login"
        className="mt-6 rounded-full bg-black px-8 py-3 text-sm font-semibold text-white shadow-lg transition-transform duration-300 hover:scale-105"
      >
        Log In
      </Link>
    </div>
    {/* Conteúdo desfocado no fundo */}
    <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <NewsCard key={index} isLoading={true} />
      ))}
    </div>
  </div>
);

const FeedPage = () => {
  const [userData, setUserData] = useState({ email: "" });
  const [initialLoading, setInitialLoading] = useState(true);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  // Função para buscar notícias baseada no filtro selecionado
  const fetchNews = useCallback(
    (page, perPage) => {
      if (!isLoggedIn && !selectedTopic) {
        return Promise.resolve({
          data: { news: [], pagination: { pages: 1 } },
        });
      }
      if (selectedTopic) {
        return newsAPI.getNewsByTopic(selectedTopic.id, page, perPage);
      } else {
        // Feed personalizado "For You" com ranking baseado em preferências do usuário
        return newsAPI.getForYouNews(page, perPage);
      }
    },
    [isLoggedIn, selectedTopic]
  ); // Dependencies for useCallback

  // Hook de infinite scroll
  const {
    data: news,
    loading: newsLoading,
    hasMore,
    error: newsError,
    lastElementRef,
    reset: resetNews,
  } = useInfiniteScroll(fetchNews, {
    perPage: 10,
  });

  useEffect(() => {
    const fetchInitialData = async () => {
      setInitialLoading(true);
      setTopicsLoading(true);

      let userIsLoggedIn = false; // Variável local para o status de login
      let fetchedTopics = []; // Variável local para os tópicos

      try {
        // Buscar dados do usuário e tópicos em paralelo
        const [userResponse, topicsResponse] = await Promise.allSettled([
          usersAPI.getUserProfile(),
          topicsAPI.getStandardTopics(),
        ]);

        // Processar dados do usuário
        if (userResponse.status === "fulfilled") {
          setUserData(userResponse.value.data);
          userIsLoggedIn = true; // Atualiza a variável local
        } else {
          console.error("Failed to fetch user data:", userResponse.reason);
          userIsLoggedIn = false; // Atualiza a variável local
        }

        if (topicsResponse.status === "fulfilled") {
          fetchedTopics = topicsResponse.value.data || [];
          setTopics(fetchedTopics); // Define o estado de tópicos
        } else {
          console.error("Failed to fetch topics:", topicsResponse.reason);
        }
      } catch (err) {
        console.error("Connection error:", err);
      } finally {
        setInitialLoading(false);
        setTopicsLoading(false);
        setIsLoggedIn(userIsLoggedIn); // Define o estado isLoggedIn uma única vez

        // Se o usuário NÃO estiver logado e houver tópicos,
        // define o primeiro tópico como selecionado por padrão.
        // Isso evita que o usuário não logado "caia" diretamente no "For You".
        if (!userIsLoggedIn && fetchedTopics.length > 0) {
          setSelectedTopic(fetchedTopics[0]);
        }
      }
    };

    fetchInitialData();
  }, []);

  // Efeito para resetar o feed quando o tópico muda
  useEffect(() => {
    resetNews();
  }, [selectedTopic, isLoggedIn]);

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* 1. Header do Feed */}
      <HeaderFeedPage userEmail={userData.email} />

      {/* Main Content Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {/* Filtros - Renderiza apenas após o carregamento inicial para evitar o "flicker" */}
        {initialLoading ? (
          // Skeleton para a área de filtros
          <div className="flex gap-4 mb-8 flex-wrap">
            <div className="mt-6 h-8 w-24 bg-gray-300 rounded-full animate-pulse" />
            <div className="mt-6 h-8 w-28 bg-gray-300 rounded-full animate-pulse" />
            <div className="mt-6 h-8 w-20 bg-gray-300 rounded-full animate-pulse" />
          </div>
        ) : (
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
            {topics.map((topic) => (
              <button
                key={topic.id}
                onClick={() => setSelectedTopic(topic)}
                className={`flex items-center gap-3 mt-6 text-gray-900 text-xs border border-black shadow-lg pl-6 pr-6 py-1 rounded-full font-montserrat transition-all duration-300 ease-in-out hover:scale-[1.01] hover:shadow-xl hover:-translate-y-0.5 cursor-pointer ${
                  selectedTopic?.id === topic.id
                    ? "bg-black text-white [font-weight:600]"
                    : "bg-white hover:bg-gray-300 [font-weight:500]"
                }`}
              >
                {topic.name.charAt(0).toUpperCase() + topic.name.slice(1)}
              </button>
            ))}
          </div>
        )}

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
        {/* Exibe a tela de login para a seção "For You" se não estiver logado */}
        {!isLoggedIn && selectedTopic === null && (
          <div className="mt-12 mb-12">
            <LoginPrompt />
          </div>
        )}
        {/* Grid para os 3 primeiros cards (Destaques) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 mb-12">
          {newsLoading && news.length === 0
            ? // Renderiza 3 cards em estado de carregamento inicial
              Array.from({ length: 3 }).map((_, index) => (
                <NewsCard key={index} isLoading={true} />
              ))
            : isLoggedIn || selectedTopic
            ? news
                .slice(0, 3)
                .map((newsItem) => (
                  <NewsCard key={newsItem.id} news={newsItem} />
                ))
            : null}
        </div>

        {/* Layout em Lista para os demais (Corpo do Feed) */}
        <div className="space-y-0">
          {newsLoading && news.length === 0
            ? Array.from({ length: 2 }).map((_, index) => (
                <NewsCard key={index} isListItem={true} isLoading={true} />
              ))
            : (isLoggedIn || selectedTopic) &&
              news.slice(3).map((newsItem, index) => {
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
                <NewsCard
                  key={`loading-${index}`}
                  isListItem={true}
                  isLoading={true}
                />
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
        {!newsLoading &&
          news.length === 0 &&
          !newsError &&
          (isLoggedIn || selectedTopic) && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">
                Nenhuma notícia encontrada.
              </p>
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
