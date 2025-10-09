import React from "react";
// Importe a imagem de teste que você adicionou na pasta assets
import TestNewsImage from "../../assets/news-placeholder.jpg";
import Test2NewsImage from "../../assets/news-placeholder-2.jpg";

const NewsCard = ({ news, isListItem = false }) => {
  // Se for um item da lista, o layout muda radicalmente
  if (isListItem) {
    return (
      <div className="flex items-start gap-4 border-b border-gray-200 hover:bg-gray-100 transition-colors cursor-pointer">
        <img
          src={TestNewsImage} // Imagem de teste
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
      </div>
    );
  }
  // Layout para os Cards de Destaque (grid-cols-3)
  return (
    <div className="text-base rounded-lg overflow-hidden hover:shadow-xl transition-shadow cursor-pointer font-montserrat">
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
  );
};

export default NewsCard;
