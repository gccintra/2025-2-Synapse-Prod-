import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { toast } from "react-toastify";

import DynamicHeader from "../components/DynamicHeader";
import NewsPageSkeleton from "../components/NewsPage/NewsPageSkeleton";
import ScrollToTopButton from "../components/ScrollToTopButton";
import { motion } from "framer-motion";

import { newsAPI } from "../services/api";
import { usersAPI } from "../services/api";
import { formatDateLong } from "../utils/dateUtils";

const NewsPage = () => {
  const { id: newsId } = useParams();
  const [articleData, setArticleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaved, setIsSaved] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState({ email: "" });
  const historyAddedRef = useRef(false);

  useEffect(() => {
    const fetchNewsData = async () => {
      if (!newsId) {
        setError("ID da notícia não fornecido");
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const [newsResponse, authResponse] = await Promise.allSettled([
          newsAPI.getNewsById(newsId),
          usersAPI.getUserProfile(),
        ]);
        if (newsResponse.status === "rejected") throw newsResponse.reason;
        const newsData = newsResponse.value.data;
        setArticleData({
          title: newsData.title,
          image: newsData.image_url || "https://via.placeholder.com/800x400",
          source: newsData.source_name || "Fonte não informada",
          date: formatDateLong(newsData.published_at) || "Data não informada",
          contentHtml:
            newsData.content ||
            newsData.description ||
            "Conteúdo não disponível",
        });

        setIsSaved(newsData.is_favorited || false);

        // status de login
        if (authResponse.status === "fulfilled") {
          setIsLoggedIn(true);
          setUserData(authResponse.value.data);
        }
      } catch (err) {
        console.error("Erro ao carregar notícia:", err);
        setError(err.message || "Erro ao carregar a notícia");
      } finally {
        setLoading(false);
      }
    };

    fetchNewsData();
  }, [newsId]);

  useEffect(() => {
    if (isLoggedIn && newsId && !historyAddedRef.current) {
      const addHistory = async () => {
        try {
          await newsAPI.addNewsToHistory(newsId);
          historyAddedRef.current = true;
        } catch (historyError) {
          console.warn("Could not save to history:", historyError.message);
        }
      };
      addHistory();
    }
  }, [isLoggedIn, newsId]);

  const createMarkup = (htmlContent) => {
    return { __html: htmlContent };
  };

  const handleSaveClick = async () => {
    if (!isLoggedIn) {
      toast.warn("To save a news story, you need to be logged in.");
      return;
    }

    if (isSaving) return;
    setIsSaving(true);
    try {
      if (isSaved) {
        await newsAPI.unfavoriteNews(newsId);
        toast.info("News removed from your favorites.");
      } else {
        await newsAPI.favoriteNews(newsId);
        toast.success("News successfully saved!");
      }
      setIsSaved(!isSaved);
    } catch (error) {
      toast.error(error.message || "Erro ao salvar notícia.");
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return <NewsPageSkeleton isLoggedIn={isLoggedIn} />;
  }

  if (error) {
    return (
      <div className="bg-white min-h-screen">
        <DynamicHeader
          userEmail={userData.email}
          isAuthenticated={isLoggedIn}
        />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-20">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Erro ao carregar notícia
            </h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => window.history.back()}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Voltar
            </button>
          </div>
        </main>
      </div>
    );
  }

  if (!articleData) {
    return (
      <div className="bg-white min-h-screen">
        <DynamicHeader
          userEmail={userData.email}
          isAuthenticated={isLoggedIn}
        />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-20">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Notícia não encontrada
            </h1>
            <p className="text-gray-600 mb-6">
              A notícia solicitada não foi encontrada.
            </p>
            <button
              onClick={() => window.history.back()}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Voltar
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <ScrollToTopButton />
      <DynamicHeader userEmail={userData.email} isAuthenticated={isLoggedIn} />
      <motion.main
        className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
      >
        <>
          {/* Imagem de Destaque */}
          <img
            src={articleData.image}
            alt={articleData.title}
            className="w-full h-96 object-cover rounded-lg mb-8 shadow-md"
          />
          {/* Título e Metadados */}
          <div className="mb-10 border-b border-gray-300 pb-4">
            <h1 className="text-4xl font-extrabold text-gray-900 font-montserrat mb-3 leading-tight">
              {articleData.title}
            </h1>
            <div className="flex justify-between items-center">
              <p className="text-base text-gray-600 font-montserrat">
                Fonte:{" "}
                <span className="font-semibold text-black">
                  {articleData.source}
                </span>{" "}
                | {articleData.date}
              </p>
              {/* ícone salvar */}
              <button
                onClick={handleSaveClick}
                disabled={isSaving}
                className={`p-2 rounded-full hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 ${
                  isSaving ? "cursor-wait" : ""
                }`}
                aria-label="Salvar notícia"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className={`h-6 w-6 transition-colors ${
                    isSaved ? "text-black" : "text-gray-500"
                  }`}
                  fill={isSaved ? "currentColor" : "none"}
                  viewBox="0 0 24 24"
                  stroke="black"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                  />
                </svg>
              </button>
            </div>
          </div>
          <style>
            {`
              .article-content img {
                display: block;
                margin-left: auto;
                margin-right: auto;
                border-radius: 0.5rem; /* Bordas arredondadas */
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); /* Sombra suave */
                margin-top: 2em;
                margin-bottom: 2em;
              }
            `}
          </style>
          <article>
            <div
              className="prose prose-lg max-w-none font-montserrat text-gray-800 article-content"
              dangerouslySetInnerHTML={createMarkup(articleData.contentHtml)}
            />
          </article>
        </>
      </motion.main>
    </div>
  );
};

export default NewsPage;
