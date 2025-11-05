import React, { forwardRef, useState } from "react";
import { Link, useLocation } from "react-router-dom"; // Import useLocation
import { toast } from "react-toastify";
import TestNewsImage from "../../assets/news-placeholder.jpg";
import Test2NewsImage from "../../assets/news-placeholder-2.jpg";
import { NewsMetadata } from "../../utils/dateUtils";
import { newsAPI } from "../../services/api";

const NewsCard = forwardRef(
  (
    {
      news,
      isListItem = false,
      isLoading = false,
      isLoggedIn = false,
      showSaveButton = true,
    },
    ref
  ) => {
    const [isSaved, setIsSaved] = useState(news?.is_favorited || false);
    const [isSaving, setIsSaving] = useState(false);
    const [isClicked, setIsClicked] = useState(false);
    const location = useLocation();
    const LinkComponent = isLoading ? "div" : Link;

    // impede que o clique no ícone navegue para a notícia
    const handleSaveClick = async (e) => {
      e.stopPropagation();
      e.preventDefault();

      // verifica se o usuário NÃO está logado
      if (!isLoggedIn) {
        toast.warn("To save a news story, you need to be logged in.");
        return; // interrompe a execução
      }

      if (isSaving) return; // previne múltiplos cliques

      setIsClicked(true); // animação
      setTimeout(() => setIsClicked(false), 300);

      setIsSaving(true);

      try {
        if (isSaved) {
          await newsAPI.unfavoriteNews(news.id);
          toast.info("News removed from your favorites.");
        } else {
          await newsAPI.favoriteNews(news.id);
          toast.success("News successfully saved!");
        }
        setIsSaved(!isSaved); // Atualiza o estado visual
      } catch (error) {
        toast.error(error.message || "Error saving news item.");
      } finally {
        setIsSaving(false);
      }
    };

    if (isListItem) {
      return (
        // card da lista
        <LinkComponent
          to={!isLoading ? `/article/${news?.id}` : undefined}
          state={{ from: location.pathname }}
          ref={ref}
          className={`relative group flex flex-row items-start gap-4 p-4 border-b border-gray-200 ${
            !isLoading && "hover:bg-gray-100 transition-colors cursor-pointer"
          }`}
        >
          {isLoading ? (
            <div className="w-24 h-24 bg-gray-300 rounded-md flex-shrink-0 animate-pulse"></div>
          ) : (
            <img
              src={news?.image_url || TestNewsImage}
              alt={news?.title}
              className="w-20 h-20 sm:w-24 sm:h-24 object-cover flex-shrink-0 rounded-md"
            />
          )}

          {/* texto */}
          <div className="flex-grow">
            {isLoading ? (
              <div className="animate-pulse">
                <div className="h-5 bg-gray-300 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-300 rounded w-full mb-1"></div>
                <div className="h-4 bg-gray-300 rounded w-5/6"></div>
              </div>
            ) : (
              <>
                <h3 className="text-sm sm:text-base font-semibold text-gray-900 mb-1 font-montserrat">
                  {news?.title}
                </h3>
                <p className="text-xs sm:text-sm text-gray-600 line-clamp-2 font-montserrat mb-2">
                  {news?.description || news?.summary}
                </p>
                <NewsMetadata
                  sourceName={news?.source_name}
                  publishedAt={news?.published_at}
                  className="text-xs font-montserrat"
                  showTimeAgo={true}
                />
              </>
            )}
          </div>

          {/* ícone salvar */}
          {!isLoading && showSaveButton && (
            <button
              onClick={handleSaveClick}
              disabled={isSaving}
              className={`hidden sm:block absolute top-3 right-3 z-10 p-1.5 text-gray-600 hover:text-black transition-all duration-200 ${
                isSaved ? "opacity-100" : "opacity-0 group-hover:opacity-100"
              } ${isSaving ? "cursor-wait" : ""}`}
              aria-label="Salvar notícia"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className={`h-5 w-5 transition-colors ${
                  isSaved ? "text-black" : "text-gray-600"
                } ${isClicked ? "animate-pop-in" : ""}`}
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
          )}
        </LinkComponent>
      );
    }
    return (
      // card destaques
      <LinkComponent
        to={!isLoading ? `/article/${news?.id}` : undefined}
        state={{ from: location.pathname }}
        className={`relative group text-sm md:text-base overflow-hidden font-montserrat h-full w-11/12 mx-auto md:w-full md:mx-0 ${
          !isLoading &&
          "cursor-pointer sm:transition-all sm:duration-300 sm:ease-in-out sm:hover:scale-[1.02]"
        }`}
      >
        <div className="mt-6 flex flex-col h-full">
          {/* imagem */}
          {isLoading ? (
            <div className="w-full h-48 bg-gray-300 animate-pulse rounded-lg flex-shrink-0"></div>
          ) : (
            <img
              src={news?.image_url || Test2NewsImage}
              alt={news?.title}
              className="w-full h-48 object-cover rounded-lg flex-shrink-0"
            />
          )}
          {/* conteúdo */}
          <div className="p-1 mt-8 flex-grow flex flex-col">
            {isLoading ? (
              <div className="animate-pulse space-y-2">
                <div className="h-5 bg-gray-300 rounded w-full mb-3"></div>
                <div className="h-3 bg-gray-300 rounded w-full"></div>
                <div className="h-3 bg-gray-300 rounded w-4/5"></div>
                <div className="h-3 bg-gray-300 rounded w-1/3 mt-4"></div>
              </div>
            ) : (
              <>
                {/* texto */}
                <h3 className="text-base font-bold text-gray-900 mb-2 font-montserrat">
                  {news?.title}
                </h3>
                <p className="text-sm text-gray-600 line-clamp-3 font-montserrat mb-3">
                  {news?.description || news?.summary}
                </p>
                <NewsMetadata
                  sourceName={news?.source_name}
                  publishedAt={news?.published_at}
                  className="text-xs font-montserrat"
                  showTimeAgo={true}
                />
              </>
            )}
          </div>
          {/* ícone salvar destaques */}
          {!isLoading && showSaveButton && (
            <button
              onClick={handleSaveClick}
              disabled={isSaving}
              className={`hidden sm:block absolute top-3 right-3 z-10 p-2 bg-white/70 backdrop-blur-sm rounded-full text-gray-700 hover:bg-white hover:text-black transition-all duration-200 ${
                isSaved ? "opacity-100" : "opacity-0 group-hover:opacity-100"
              } ${isSaving ? "cursor-wait" : ""}`}
              aria-label="Salvar notícia"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className={`h-5 w-5 transition-colors ${
                  isSaved ? "text-black" : "text-gray-600"
                } ${isClicked ? "animate-pop-in" : ""}`} // E aqui também
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
          )}
        </div>
      </LinkComponent>
    );
  }
);

NewsCard.displayName = "NewsCard";

export default NewsCard;
