// src/components/SavedNews/SavedNewsCardSkeleton.jsx

import React from "react";

const SavedNewsCardSkeleton = () => {
  return (
    <div className="w-full rounded-lg overflow-hidden shadow-md bg-white animate-pulse">
      {/* Imagem */}
      <div className="w-full h-36 sm:h-50 bg-gray-300"></div>

      {/* Container de Texto */}
      <div className="p-4 space-y-3">
        {/* Título */}
        <div className="h-4 bg-gray-300 rounded w-3/4"></div>
        <div className="h-4 bg-gray-300 rounded w-1/2"></div>

        {/* espaçador */}
        <div className="h-2"></div>

        {/* Resumo */}
        <div className="h-3 bg-gray-300 rounded w-full"></div>
        <div className="h-3 bg-gray-300 rounded w-full"></div>
        <div className="h-3 bg-gray-300 rounded w-4/5"></div>
      </div>
    </div>
  );
};

export default SavedNewsCardSkeleton;
