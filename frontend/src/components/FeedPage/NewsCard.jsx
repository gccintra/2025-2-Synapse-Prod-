import React, { forwardRef } from "react";
import { Link } from "react-router-dom";
import TestNewsImage from "../../assets/news-placeholder.jpg";
import Test2NewsImage from "../../assets/news-placeholder-2.jpg";
import { NewsMetadata } from "../../utils/dateUtils";

const NewsCard = forwardRef(({ news, isListItem = false, isLoading = false }, ref) => {
  const LinkComponent = isLoading ? "div" : Link;

  if (isListItem) {
    return (
      // Card da lista
      <LinkComponent
        to={!isLoading ? `/article/${news?.id}` : undefined}
        ref={ref}
        className={`flex items-start gap-4 p-4 border-b border-gray-200 ${
          !isLoading && "hover:bg-gray-100 transition-colors cursor-pointer"
        }`}
      >
        {isLoading ? (
          <div className="w-24 h-24 bg-gray-300 rounded-md flex-shrink-0 animate-pulse"></div>
        ) : (
          <img
            src={news?.image_url || TestNewsImage}
            alt={news?.title}
            className="w-24 h-24 object-cover flex-shrink-0 rounded-md"
          />
        )}

        {/* Texto */}
        <div className="flex-grow">
          {isLoading ? (
            <div className="animate-pulse">
              <div className="h-5 bg-gray-300 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-300 rounded w-full mb-1"></div>
              <div className="h-4 bg-gray-300 rounded w-5/6"></div>
            </div>
          ) : (
            <>
              <h3 className="text-base font-semibold text-gray-900 mb-1 font-montserrat">
                {news?.title}
              </h3>
              <p className="text-sm text-gray-600 line-clamp-2 font-montserrat mb-2">
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
      </LinkComponent>
    );
  }
  return (
    // Card destaques
    <LinkComponent
      to={!isLoading ? `/article/${news?.id}` : undefined}
      className={`text-base rounded-lg overflow-hidden font-montserrat h-full ${
        !isLoading &&
        "transition-all duration-300 ease-in-out hover:scale-[1.02] cursor-pointer"
      }`}
    >
      <div>
        {/* Imagem */}
        {isLoading ? (
          <div className="w-full h-48 bg-gray-300 animate-pulse"></div>
        ) : (
          <img
            src={news?.image_url || Test2NewsImage}
            alt={news?.title}
            className="w-full h-48 object-cover"
          />
        )}
        <div className="mt-3">
          {isLoading ? (
            <div className="animate-pulse">
              <div className="h-6 bg-gray-300 rounded w-full mb-3"></div>
              <div className="h-4 bg-gray-300 rounded w-full mb-1"></div>
              <div className="h-4 bg-gray-300 rounded w-5/6"></div>
            </div>
          ) : (
            <>
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
      </div>
    </LinkComponent>
  );
});

export default NewsCard;
