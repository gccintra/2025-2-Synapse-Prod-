// src/pages/NewsPage.jsx

import React, { useState, useEffect } from "react";
import HeaderNewsPage from "../components/NewsPage/HeaderNewsPage";
import NewsPageSkeleton from "../components/NewsPage/NewsPageSkeleton";
import { useParams } from "react-router-dom";
import { newsAPI } from "../services/api";
import { formatDateLong } from "../utils/dateUtils";

const NewsPage = () => {
  const { id: newsId } = useParams();
  const [articleData, setArticleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaved, setIsSaved] = useState(false);

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

        const response = await newsAPI.getNewsById(newsId);
        const newsData = response.data;

        // Adaptar os dados da API para o formato esperado
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
      } catch (err) {
        console.error("Erro ao carregar notícia:", err);
        setError(err.message || "Erro ao carregar a notícia");
      } finally {
        setLoading(false);
      }
    };

    fetchNewsData();
  }, [newsId]);

  // Função de segurança para HTML
  const createMarkup = (htmlContent) => {
    return { __html: htmlContent };
  };

  // Função para lidar com o clique no botão de salvar
  const handleSaveClick = () => {
    setIsSaved(!isSaved);
  };

  if (loading) {
    return <NewsPageSkeleton />;
  }

  if (error) {
    return (
      <div className="bg-white min-h-screen">
        <HeaderNewsPage />
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
        <HeaderNewsPage />
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
    <div className="bg-white min-h-screen">
      {/* Header da Página de Notícias (mantendo o email do usuário) */}
      <HeaderNewsPage />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 pb-20">
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

            {/* --- ÍCONE DE SALVAR --- */}
            <button
              onClick={handleSaveClick}
              className="p-2 rounded-full hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400"
              aria-label="Salvar notícia"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className={`h-6 w-6 ${
                  isSaved ? "text-black" : "text-gray-600"
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

        {/* 🛑 Conteúdo do Artigo com dangerouslySetInnerHTML 🛑 */}
        <article>
          {/* A classe 'prose' do Tailwind é crucial aqui para aplicar estilos de leitura padrão ao HTML que vem da API (p, h2, img, a, etc.) */}
          <div
            className="prose prose-lg max-w-none font-montserrat text-gray-800"
            dangerouslySetInnerHTML={createMarkup(articleData.contentHtml)}
          />
        </article>
      </main>
    </div>
  );
};

export default NewsPage;
