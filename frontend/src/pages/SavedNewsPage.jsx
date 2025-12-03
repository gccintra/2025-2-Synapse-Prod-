import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";

import SavedNewsCard from "../components/SavedNews/SavedNewsCard";
import DynamicHeader from "../components/DynamicHeader";
import SavedNewsCardSkeleton from "../components/SavedNews/SavedNewsCardSkeleton";
import ScrollToTopButton from "../components/ScrollToTopButton";
import RemoveConfirmationModal from "../components/SavedNews/RemoveConfirmationModal";
import { useAuthContext } from "../contexts/AuthContext";

import { newsAPI } from "../services/api";

const SavedNewsPage = () => {
  const { user } = useAuthContext();
  const [savedNews, setSavedNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [newsToRemove, setNewsToRemove] = useState(null);

  // animações
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
    const fetchSavedNews = async () => {
      setLoading(true);
      setError(null);
      try {
        const savedNewsResponse = await newsAPI.getSavedNews();

        if (savedNewsResponse.success) {
          const newsData = savedNewsResponse.data?.news || [];
          const mappedNews = newsData.map((newsItem) => ({
            id: newsItem.id,
            title: newsItem.title,
            summary: newsItem.description,
            image: newsItem.image_url,
          }));
          setSavedNews(mappedNews);
        } else {
          throw new Error("Failed to load saved news.");
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
        setError(error.message || "An unexpected error occurred.");
      }
      setLoading(false);
    };

    fetchSavedNews();
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
      <DynamicHeader
        userEmail={user?.email || ""}
        isAuthenticated={true}
        backTo="/feed"
        backText="Back to feed"
      />

      <main className="flex-grow max-w-6xl mx-auto sm:px-6 lg:px-8 mt-12 w-full">
        <h1 className="p-3 text-2xl sm:text-3xl font-medium text-gray-900 font-montserrat text-center">
          Your saved news
        </h1>

        {loading ? (
          <div className="hidden md:flex flex-wrap justify-center gap-8 mt-12 p-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="w-full sm:w-1/2 lg:w-[30%] xl:w-1/4">
                <SavedNewsCardSkeleton />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-16">
            <h2 className="text-xl font-semibold text-red-600 mb-4">
              Oops! Something went wrong.
            </h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-black text-white font-bold py-2 px-4 rounded hover:bg-gray-800 transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : savedNews.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-xl text-gray-600 mb-6">
              You haven't saved any news yet.
            </p>
            <Link
              to="/feed"
              className="bg-black text-white font-bold py-3 px-6 rounded-full hover:bg-gray-800 transition-transform hover:scale-105 inline-block"
            >
              Explore the Feed
            </Link>
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
                  className="w-1/3 lg:w-[30%]"
                >
                  <SavedNewsCard news={news} onRemove={handleConfirmRemove} />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </main>
      <ScrollToTopButton />

      <RemoveConfirmationModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConfirm={handleRemoveNews}
      />
    </div>
  );
};

export default SavedNewsPage;
