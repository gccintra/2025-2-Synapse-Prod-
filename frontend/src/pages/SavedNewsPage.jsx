import React, { useState, useEffect } from "react";
import HeaderEditAccount from "../components/HeaderEditAccount";
import SavedNewsCard from "../components/SavedNews/SavedNewsCard";
import RemoveConfirmationModal from "../components/SavedNews/RemoveConfirmationModal";
import SavedNewsCardSkeleton from "../components/SavedNews/SavedNewsCardSkeleton";
import { usersAPI, newsAPI } from "../services/api";

const SavedNewsPage = () => {
  const [savedNews, setSavedNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newsToRemove, setNewsToRemove] = useState(null);
  const [userData, setUserData] = useState({ email: "" });

  useEffect(() => {
    const fetchPageData = async () => {
      setLoading(true);
      try {
        const userProfile = await usersAPI.getUserProfile();
        setUserData(userProfile.data);

        const savedNewsResponse = await newsAPI.getSavedNews();

        if (
          savedNewsResponse &&
          savedNewsResponse.data &&
          Array.isArray(savedNewsResponse.data.news)
        ) {
          const mappedNews = savedNewsResponse.data.news.map((newsItem) => ({
            id: newsItem.id,
            title: newsItem.title,
            summary: newsItem.description,
            image: newsItem.image_url,
            isSaved: newsItem.is_favorited,
          }));
          setSavedNews(mappedNews);
        } else {
          setSavedNews([]);
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
        setSavedNews([]);
      }
      setLoading(false);
    };

    fetchPageData();
  }, []);

  const handleConfirmRemove = (newsId) => {
    setNewsToRemove(newsId);
    setShowModal(true);
  };

  const handleRemoveNews = async () => {
    if (newsToRemove) {
      setShowModal(false);
      try {
        await newsAPI.unfavoriteNews(newsToRemove);
        setSavedNews((prevNews) =>
          prevNews.filter((news) => news.id !== newsToRemove)
        );
        console.log(`Notícia ${newsToRemove} removida com sucesso.`);
      } catch (error) {
        console.error("Failed to remove news from backend:", error);
      }
      setNewsToRemove(null);
    }
  };

  return (
    <div className="bg-gray-50 min-h-screen flex flex-col font-montserrat">
      <HeaderEditAccount userEmail={userData.email} />

      <main className="flex-grow max-w-6xl mx-auto sm:px-6 lg:px-8 mt-12 w-full">
        <h1 className="p-3 text-3xl font-medium text-gray-900 font-montserrat text-center">
          Your saved news
        </h1>

        {loading ? (
          <div className="flex flex-wrap justify-center gap-8 mt-12 p-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="w-full sm:w-1/2 md:w-1/3 lg:w-[30%] xl:w-1/4"
              >
                <SavedNewsCardSkeleton />
              </div>
            ))}
          </div>
        ) : savedNews.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-xl text-gray-600 mb-4">
              Você ainda não salvou nenhuma notícia.
            </p>
          </div>
        ) : (
          <div className="p-4 flex flex-wrap justify-center gap-8 mt-12">
            {savedNews.map((news) => (
              <div
                key={news.id}
                className="w-full sm:w-1/2 md:w-1/3 lg:w-[30%] xl:w-1/4"
              >
                <SavedNewsCard news={news} onRemove={handleConfirmRemove} />
              </div>
            ))}
          </div>
        )}
      </main>

      <RemoveConfirmationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConfirm={handleRemoveNews}
      />
    </div>
  );
};

export default SavedNewsPage;
