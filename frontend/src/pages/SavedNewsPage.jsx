import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SavedNewsCard from "../components/SavedNews/SavedNewsCard";
import DynamicHeader from "../components/DynamicHeader"; // Import the new DynamicHeader
import RemoveConfirmationModal from "../components/SavedNews/RemoveConfirmationModal";
import SavedNewsCardSkeleton from "../components/SavedNews/SavedNewsCardSkeleton";
import { usersAPI, newsAPI } from "../services/api";

const SavedNewsPage = () => {
  const [savedNews, setSavedNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newsToRemove, setNewsToRemove] = useState(null);
  const [userData, setUserData] = useState({ email: "" });

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.07,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

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
      <DynamicHeader userEmail={userData.email} isAuthenticated={true} />

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
          <motion.div
            layout
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="p-4 flex flex-wrap justify-center gap-8 mt-12"
          >
            <AnimatePresence>
              {savedNews.map((news) => (
                <motion.div
                  key={news.id}
                  variants={itemVariants}
                  layout
                  exit={{
                    opacity: 0,
                    scale: 0.5,
                    transition: { duration: 0.2 },
                  }}
                  className="w-full sm:w-1/2 md:w-1/3 lg:w-[30%] xl:w-1/4"
                >
                  <SavedNewsCard news={news} onRemove={handleConfirmRemove} />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
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
