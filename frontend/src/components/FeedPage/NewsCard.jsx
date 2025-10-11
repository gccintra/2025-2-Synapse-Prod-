import React from "react";
import { Link } from "react-router-dom";
import TestNewsImage from "../../assets/news-placeholder.jpg";
import Test2NewsImage from "../../assets/news-placeholder-2.jpg";

const NewsCard = ({ news, isListItem = false }) => {
  if (isListItem) {
    return (
      // Card da lista
      <Link
        to={`/article/${news.id}`}
        className="flex items-start gap-4 border-b border-gray-200 hover:bg-gray-200 transition-colors cursor-pointer"
      >
        <img
          src={TestNewsImage}
          alt={news.title}
          className="w-18 h-16 mb-4 object-cover flex-shrink-0 rounded-md"
        />

        {/* Texto */}
        <div className="flex-grow">
          <h3 className="text-base font-semibold text-gray-900 mb-1 font-montserrat">
            {news.title}
          </h3>
          <p className="text-xs text-gray-600 line-clamp-2 font-montserrat">
            {news.summary}
          </p>
        </div>
      </Link>
    );
  }
  return (
    // Card destaques
    <Link to={`/article/${news.id}`}>
      <div className="text-base rounded-lg overflow-hidden transition-all duration-300 ease-in-out hover:scale-[1.02] cursor-pointer font-montserrat h-full">
        {/* Imagem */}
        <img
          src={Test2NewsImage} // Imagem de teste
          alt={news.title}
          className="w-full h-48 object-cover"
        />
        <div className="mt-3">
          <h3 className="text-base font-bold text-gray-900 mb-2 font-montserrat">
            {news.title}
          </h3>
          <p className="text-xs text-gray-600 line-clamp-3 font-montserrat">
            {news.summary}
          </p>
        </div>
      </div>
    </Link>
  );
};

export default NewsCard;
