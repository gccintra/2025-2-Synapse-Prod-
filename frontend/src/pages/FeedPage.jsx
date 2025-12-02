import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link, useLocation } from "react-router-dom";

import { useInfiniteScroll } from "../hooks/useInfiniteScroll";
import ScrollToTopButton from "../components/ScrollToTopButton";
import { motion, AnimatePresence } from "framer-motion";

import NewsCard from "../components/FeedPage/NewsCard";
import DynamicHeader from "../components/DynamicHeader";

import { topicsAPI, usersAPI, newsAPI } from "../services/api";

const LoginPrompt = () => (
  <div className="relative min-h-[400px] overflow-hidden">
    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-lg bg-white/20 p-4 text-center sm:p-8">
      <h2 className="text-base font-bold text-gray-900 font-montserrat sm:text-xl">
        Access your personalized feed
      </h2>
      <p className="mt-2 text-xs sm:text-sm text-gray-700 font-montserrat">
        Please log in to see the news tailored specifically for you.
      </p>
      <Link
        to="/login"
        className="mt-6 bg-black text-white font-medium sm:font-bold py-2 px-3 sm:py-2 sm:px-4 rounded sm:hover:bg-gray-800 font-montserrat text-xs sm:text-sm transition-transform duration-300 hover:scale-105"
      >
        Login
      </Link>
    </div>
    <div className="grid grid-cols-1 gap-6 sm:gap-8 md:grid-cols-3 filter blur-sm grayscale scale-95 opacity-70">
      {Array.from({ length: 3 }).map((_, index) => (
        <div key={index} className={index > 0 ? "hidden md:block" : "block"}>
          <NewsCard isLoading={true} />
        </div>
      ))}
    </div>
  </div>
);

const TopicSelector = React.forwardRef(
  ({ topics, selectedTopic, onSelectTopic, isLoading }, ref) => {
    if (isLoading) {
      return (
        <div className="flex gap-4 mb-8 flex-wrap">
          <div className="mt-6 h-8 w-24 bg-gray-300 rounded-full animate-pulse" />
          <div className="mt-6 h-8 w-28 bg-gray-300 rounded-full animate-pulse" />
          <div className="mt-6 h-8 w-20 bg-gray-300 rounded-full animate-pulse" />
        </div>
      );
    }

    return (
      <motion.div
        ref={ref}
        className="flex gap-4 mb-8 cursor-grab select-none custom-scroll overflow-x-auto flex-nowrap w-11/12 mx-auto md:w-full md:mx-0"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* botão for you */}
        <TopicButton
          label="For You"
          isSelected={selectedTopic === null}
          onClick={() => onSelectTopic(null)}
        />

        {/* tópicos padrão */}
        {topics.map((topic) => (
          <TopicButton
            key={topic.id}
            label={topic.name.charAt(0).toUpperCase() + topic.name.slice(1)}
            isSelected={selectedTopic?.id === topic.id}
            onClick={() => onSelectTopic(topic)}
          />
        ))}
      </motion.div>
    );
  }
);
TopicSelector.displayName = "TopicSelector";

// animações do container e dos itens
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
};
const TopicButton = ({ label, isSelected, onClick }) => (
  <motion.button
    onClick={onClick}
    className="relative flex-shrink-0 flex items-center gap-3 mt-6 text-xs border border-black shadow-lg pl-6 pr-6 py-1 rounded-full font-montserrat transition-colors duration-300"
    animate={{
      color: isSelected ? "#fff" : "#000",
      fontWeight: isSelected ? "600" : "500",
    }}
  >
    <span className="relative z-10">{label}</span>
    {isSelected && (
      <motion.div
        className="absolute inset-0 bg-black rounded-full"
        layoutId="active-pill"
        transition={{ type: "spring", stiffness: 350, damping: 30 }}
        style={{ zIndex: 0 }}
      />
    )}
  </motion.button>
);

// animações do container e dos itens
const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { duration: 0.5 } },
};

const FeedPage = () => {
  const [userData, setUserData] = useState({ email: "" });
  const [initialLoading, setInitialLoading] = useState(true);
  const [topics, setTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicsLoading, setTopicsLoading] = useState(true);
  const topicsContainerRef = useRef(null);
  const [showLeftGradient, setShowLeftGradient] = useState(false);
  const [showRightGradient, setShowRightGradient] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const location = useLocation();
  const [activeCategory, setActiveCategory] = useState(
    location.state?.activeCategory || "For You"
  );

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
        return newsAPI.getForYouNews(page, perPage);
      }
    },
    [isLoggedIn, selectedTopic]
  );

  // infinite scroll
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

      let currentUserIsLoggedIn = false;
      let currentFetchedTopics = [];

      try {
        // chamadas em paralelo
        const [userResponse, topicsResponse] = await Promise.allSettled([
          usersAPI.getUserProfile(),
          topicsAPI.getStandardTopics(),
        ]);

        // resposta do Usuário
        if (userResponse.status === "fulfilled") {
          setUserData(userResponse.value.data);
          currentUserIsLoggedIn = true;
        } else {
          currentUserIsLoggedIn = false;
        }

        // resposta dos Tópicos
        if (topicsResponse.status === "fulfilled") {
          currentFetchedTopics = topicsResponse.value.data || [];
          setTopics(currentFetchedTopics);
        }
      } catch (err) {
        console.error("Erro crítico na inicialização:", err);
      } finally {
        // estados de login e loading atualizados
        setIsLoggedIn(currentUserIsLoggedIn);
        setInitialLoading(false);
        setTopicsLoading(false);

        // LÓGICA DE SELEÇÃO DO TÓPICO INICIAL
        let topicToSelect;

        // Passo A: Define o padrão baseado no login
        if (currentUserIsLoggedIn) {
          topicToSelect = null; // Padrão para logado: "For You"
        } else {
          topicToSelect =
            currentFetchedTopics.length > 0 ? currentFetchedTopics[0] : null; // Padrão para não logado: Primeiro tópico
        }

        // Passo B: Tenta sobrescrever com o histórico de navegação, se existir
        if (location.state?.activeCategory && currentFetchedTopics.length > 0) {
          if (location.state.activeCategory === "For You") {
            // Se veio de "For You", só permite se estiver logado
            if (currentUserIsLoggedIn) {
              topicToSelect = null;
            }
          } else {
            // Tenta encontrar o tópico pelo nome
            const restoredTopic = currentFetchedTopics.find(
              (t) => t.name === location.state.activeCategory
            );
            if (restoredTopic) {
              topicToSelect = restoredTopic;
            }
          }
        }

        // Passo C: Aplica a seleção final
        setSelectedTopic(topicToSelect);
      }
    };

    fetchInitialData();
  }, []);

  // resetar o feed quando o tópico muda
  useEffect(() => {
    resetNews();
  }, [selectedTopic, isLoggedIn]);

  // efeito que controla o carrossel de tópicos (gradientes e drag-to-scroll)
  useEffect(() => {
    const slider = topicsContainerRef.current;
    if (!slider) return;

    const handleScrollAndResize = () => {
      const tolerance = 2;
      const hasOverflow = slider.scrollWidth > slider.clientWidth + tolerance;

      if (hasOverflow) {
        setShowLeftGradient(slider.scrollLeft > 0);
        setShowRightGradient(
          slider.scrollLeft <
            slider.scrollWidth - slider.clientWidth - tolerance
        );
      } else {
        setShowLeftGradient(false);
        setShowRightGradient(false);
      }
    };

    let isDown = false;
    let startX;
    let scrollLeft;

    const handleMouseDown = (e) => {
      isDown = true;
      slider.classList.add("cursor-grabbing");
      startX = e.pageX - slider.offsetLeft;
      scrollLeft = slider.scrollLeft;
    };

    const handleMouseLeave = () => {
      isDown = false;
      slider.classList.remove("cursor-grabbing");
    };

    const handleMouseUp = () => {
      isDown = false;
      slider.classList.remove("cursor-grabbing");
    };

    const handleMouseMove = (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - slider.offsetLeft;
      const walk = (x - startX) * 2; // Multiplicador para acelerar o arraste
      slider.scrollLeft = scrollLeft - walk;
    };

    // Adiciona todos os event listeners
    slider.addEventListener("scroll", handleScrollAndResize);
    window.addEventListener("resize", handleScrollAndResize);
    slider.addEventListener("mousedown", handleMouseDown);
    slider.addEventListener("mouseleave", handleMouseLeave);
    slider.addEventListener("mouseup", handleMouseUp);
    slider.addEventListener("mousemove", handleMouseMove);

    // Executa a verificação inicial
    handleScrollAndResize();

    // Função de limpeza para remover todos os listeners
    return () => {
      slider.removeEventListener("mousedown", handleMouseDown);
      slider.removeEventListener("mouseleave", handleMouseLeave);
      slider.removeEventListener("mouseup", handleMouseUp);
      slider.removeEventListener("mousemove", handleMouseMove);
      slider.removeEventListener("scroll", handleScrollAndResize);
      window.removeEventListener("resize", handleScrollAndResize);
    };
  }, [topicsLoading, topics]); // Depende dos tópicos para recalcular o overflow

  return (
    <motion.div
      className="bg-gray-50 min-h-screen"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Dynamic Header for Feed Page */}
      <DynamicHeader
        className="relative z-index"
        userEmail={userData.email}
        isAuthenticated={isLoggedIn}
        showBackButton={false}
      />

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {/* Skeleton Loading */}
        <div className="relative">
          <TopicSelector
            ref={topicsContainerRef}
            topics={topics}
            selectedTopic={selectedTopic}
            onSelectTopic={setSelectedTopic}
            isLoading={initialLoading}
          />
          <AnimatePresence>
            {showLeftGradient && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute top-0 left-0 h-full w-16 bg-gradient-to-r from-gray-50 to-transparent pointer-events-none z-10"
              />
            )}
          </AnimatePresence>
          {showRightGradient && (
            <div className="absolute top-0 right-0 h-full w-16 bg-gradient-to-l from-gray-50 to-transparent pointer-events-none z-10" />
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
        {/* Exibe a tela de login para a seção "For You" se não estiver logado */}
        {!isLoggedIn && selectedTopic === null && (
          <div className="mt-12 mb-12">
            <LoginPrompt />
          </div>
        )}

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={!initialLoading && news.length > 0 ? "visible" : "hidden"}
        >
          {/* grid destaques */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 mb-12"
            variants={itemVariants}
          >
            {newsLoading && news.length === 0
              ? Array.from({ length: 3 }).map((_, index) => (
                  <NewsCard key={index} isLoading={true} />
                ))
              : (isLoggedIn || selectedTopic) &&
                news
                  .slice(0, 3)
                  .map((newsItem) => (
                    <NewsCard
                      key={newsItem.id}
                      news={newsItem}
                      isLoggedIn={isLoggedIn}
                      activeCategory={
                        selectedTopic ? selectedTopic.name : "For You"
                      }
                    />
                  ))}
          </motion.div>

          {/* lista */}
          <motion.div className="space-y-4" variants={itemVariants}>
            {newsLoading && news.length === 0
              ? // skeleton lista
                Array.from({ length: 4 }).map((_, index) => (
                  <NewsCard key={index} isListItem={true} isLoading={true} />
                ))
              : (isLoggedIn || selectedTopic) &&
                news.slice(3).map((newsItem, index) => {
                  const isLastItem = index === news.slice(3).length - 1;
                  return (
                    <div key={newsItem.id} className="flex md:flex-row">
                      <NewsCard
                        news={newsItem}
                        isListItem={true}
                        showSaveButton={isLoggedIn}
                        isLoggedIn={isLoggedIn}
                        ref={isLastItem ? lastElementRef : null}
                        activeCategory={
                          selectedTopic ? selectedTopic.name : "For You"
                        }
                      />
                    </div>
                  );
                })}
          </motion.div>
        </motion.div>

        {/* Indicador de carregamento para infinite scroll */}
        {newsLoading && news.length > 0 && (
          <div className="flex justify-center py-8">
            <div className="space-y-4 w-full">
              <NewsCard isListItem={true} isLoading={true} />
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
      <ScrollToTopButton />
    </motion.div>
  );
};

export default FeedPage;
