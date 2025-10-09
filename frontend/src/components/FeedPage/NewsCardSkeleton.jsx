import React from "react";

const NewsCardSkeleton = ({ type = "medium" }) => {
  const baseClasses = " rounded-lg shadow-md animate-pulse";

  // Esqueleto para o layout de lista
  if (type === "list") {
    return (
      <div className="flex items-start gap-4 p-4 border-b border-gray-200">
        <div className="w-16 h-16 bg-gray-300 rounded-md flex-shrink-0"></div>
        <div className="flex-grow">
          <div className="h-4 rounded w-3/4 mb-2"></div>
          <div className="h-4 rounded w-full mb-1"></div>
          <div className="h-4 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  // Esqueleto para os Cards de Destaque (medium ou large)
  return (
    <div className={`${baseClasses}`}>
      {/* Área da Imagem */}
      <div className="w-full h-48 bg-gray-300"></div>
      <div className="p-4">
        {/* Área do Título */}
        <div className="h-6 rounded w-full mb-3"></div>
        {/* Área do Sumário */}
        <div className="h-4 rounded w-full mb-1"></div>
        <div className="h-4 rounded w-5/6"></div>
        <div className="h-4 rounded w-3/4"></div>
      </div>
    </div>
  );
};

export default NewsCardSkeleton;
