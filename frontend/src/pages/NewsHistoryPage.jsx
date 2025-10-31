import React, { useState, useEffect } from "react";
import NewsCard from "../components/FeedPage/NewsCard";
import DynamicHeader from "../components/DynamicHeader"; // Import the new DynamicHeader
import { newsAPI, usersAPI } from "../services/api";
import { toast } from "react-toastify";

const NewsHistoryPage = () => {
  const [historyData, setHistoryData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError(null);

      try {
        // erifica se o usuário está logado e obtém o e-mail
        const profileRes = await usersAPI.getUserProfile();
        setIsLoggedIn(true);
        setUserEmail(profileRes.data.email);

        // login bem-sucedido, busca o histórico em um bloco separado
        try {
          const historyRes = await newsAPI.getHistory();
          const historyList = historyRes.data.news || [];
          const groupedData = groupHistoryByDate(historyList);
          setHistoryData(groupedData);
        } catch (historyError) {
          console.error("Failed to fetch history:", historyError);
          setError(
            "Could not load your reading history. Please try again later."
          );
          toast.error("Could not load your reading history.");
        }
      } catch (err) {
        // Se o `getUserProfile` falhar, o usuário NÃO está logado
        setIsLoggedIn(false);
        setError("You must be logged in to view your news history.");
        toast.warn("You must be logged in to view your news history.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const groupHistoryByDate = (historyList) => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const formatDateGroup = (viewedAt) => {
      const date = new Date(viewedAt); // Agora 'viewedAt' é na verdade 'read_at'
      if (date.toDateString() === today.toDateString()) return "Today";
      if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
      if (today.getTime() - date.getTime() < 7 * 24 * 60 * 60 * 1000) {
        return date.toLocaleDateString("en-US", { weekday: "long" });
      }
      return date.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    };

    const groupedData = {};

    historyList.forEach((news) => {
      const groupKey = formatDateGroup(news.read_at); // Usar news.read_at
      if (!groupedData[groupKey]) {
        groupedData[groupKey] = [];
      }
      groupedData[groupKey].push(news);
    });
    return groupedData;
  };

  return (
    <div className="bg-white min-h-screen">
      <DynamicHeader
        userEmail={userEmail}
        isAuthenticated={isLoggedIn}
        backTo="/feed"
        backText="Back to feed"
      />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 font-montserrat">
        {/* Título da Página */}
        <h1 className="p-3 text-3xl font-medium text-gray-900 font-montserrat text-center">
          News History
        </h1>

        {/* Seção de Histórico */}
        <div className="mt-11">
          {loading ? (
            <div className="space-y-12">
              {/* Bloco de esqueleto 1 (ex: "Today") */}
              <section>
                <div className="h-7 w-1/4 bg-gray-200 rounded-md animate-pulse mb-6"></div>
                <div className="space-y-0">
                  <NewsCard isListItem={true} isLoading={true} />
                  <NewsCard isListItem={true} isLoading={true} />
                </div>
              </section>

              {/* Bloco de esqueleto 2 (ex: "Yesterday") */}
              <section>
                <div className="h-7 w-1/3 bg-gray-200 rounded-md animate-pulse mb-6"></div>
                <div className="space-y-0">
                  <NewsCard isListItem={true} isLoading={true} />
                  <NewsCard isListItem={true} isLoading={true} />
                  <NewsCard isListItem={true} isLoading={true} />
                </div>
              </section>
            </div>
          ) : error ? (
            <div className="text-center py-10">
              <p className="text-gray-600">{error}</p>
            </div>
          ) : Object.keys(historyData).length === 0 ? (
            <div className="text-center py-10">
              <p className="text-gray-600">Your reading history is empty.</p>
              <p className="text-sm text-gray-500 mt-2">
                Start reading news to see your history here.
              </p>
            </div>
          ) : (
            <div className="space-y-12">
              {Object.keys(historyData).map((dateGroup) => (
                <section key={dateGroup}>
                  <h2 className="text-xl font-montserrat font-normal text-gray-900 mb-6">
                    {dateGroup}
                  </h2>

                  <div className="space-y-0">
                    {historyData[dateGroup].map((news) => (
                      <NewsCard // Usar news.read_at para a chave
                        key={`${news.id}-${news.read_at}`}
                        isListItem={true}
                        isLoggedIn={isLoggedIn}
                        showSaveButton={false}
                        news={news}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default NewsHistoryPage;
