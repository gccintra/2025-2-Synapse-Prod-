import React from "react";
import { Link } from "react-router-dom";

const HistoryNewsItem = ({ news, showBorder }) => {
  return (
    <Link to={`/article/${news.id}`} className="block group">
      <div className="flex items-start gap-5 ">
        {/* Imagem */}
        <img
          src={news.image}
          alt={news.title}
          className="w-32 h-24 object-cover rounded-md flex-shrink-0"
        />

        {/* Conteúdo de Texto */}
        <div
          className={`flex-grow ${
            showBorder ? "border-b border-gray-200 pb-6 " : "pb-6"
          }`}
        >
          <h3 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-black/70 transition-colors">
            {news.title}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-3">{news.summary}</p>
        </div>
      </div>
    </Link>
  );
};

export default HistoryNewsItem;
