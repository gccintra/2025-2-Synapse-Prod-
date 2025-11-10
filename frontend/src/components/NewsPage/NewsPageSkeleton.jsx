import React from "react";

const NewsPageSkeleton = () => {
  return (
    <div className="bg-white min-h-screen">
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-20">
        <div className="animate-pulse">
          {/* Placeholder da Imagem de Destaque */}
          <div className="w-full h-96 bg-gray-300 rounded-lg mb-8 shadow-md"></div>

          {/* Placeholder do Título e Metadados */}
          <div className="mb-10 border-b border-gray-300 pb-4">
            <div className="h-10 bg-gray-300 rounded w-full mb-4"></div>
            <div className="h-8 bg-gray-300 rounded w-3/4 mb-4"></div>
            <div className="h-6 bg-gray-300 rounded w-1/2"></div>
          </div>

          {/* Placeholder do Conteúdo do Artigo */}
          <div className="space-y-4">
            <div className="h-4 bg-gray-300 rounded w-full"></div>
            <div className="h-4 bg-gray-300 rounded w-full"></div>
            <div className="h-4 bg-gray-300 rounded w-5/6"></div>
            <div className="h-4 bg-gray-300 rounded w-full mt-6"></div>
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <br />
            <div className="h-4 bg-gray-300 rounded w-full"></div>
            <div className="h-4 bg-gray-300 rounded w-4/5"></div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default NewsPageSkeleton;
