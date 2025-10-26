import React, { useState, useEffect } from "react";
import HeaderFeedPage from "../components/FeedPage/HeaderFeedPage";
import NewsCard from "../components/FeedPage/NewsCard"; // 1. Importar o NewsCard

const MOCK_HISTORY_DATA = [
  {
    id: 1,
    title: "Google completa 27 anos com doodle especial",
    summary: "Lorem ipsum dolor sit amet, consectetur...",
    image: "https://via.placeholder.com/150x100",
    readAt: new Date(Date.now() - 86400000 * 2),
    source_name: "Google News",
  },
  {
    id: 2,
    title: "Astrônomos detectam anã branca que ...",
    summary: "Lorem ipsum dolor sit amet, consectetur...",
    image: "https://via.placeholder.com/150x100",
    readAt: new Date(Date.now() - 86400000 * 2),
    source_name: "BBC",
  },
  {
    id: 3,
    title: "What's the big deal about AI data centres?",
    summary: "Lorem ipsum dolor sit amet, consectetur...",
    image: "https://via.placeholder.com/150x100",
    readAt: new Date(Date.now() - 86400000 * 5),
    source_name: "Wired",
  },
  {
    id: 4,
    title: "The airliner pilot who gets to fly...",
    summary: "Lorem ipsum dolor sit amet, consectetur...",
    image: "https://via.placeholder.com/150x100",
    readAt: new Date(Date.now() - 86400000 * 5),
    source_name: "The Verge",
  },
  {
    id: 5,
    title: "A resposta oficial da Apple aos arranhões...",
    summary: "Lorem ipsum dolor sit amet, consectetur...",
    image: "https://via.placeholder.com/150x100",
    readAt: new Date("2025-10-16T10:00:00Z"),
    source_name: "Apple News",
  },
];

const NewsHistoryPage = () => {
  const [historyData, setHistoryData] = useState({});
  const [loading, setLoading] = useState(true);

  const userEmail = "";

  useEffect(() => {
    const data = MOCK_HISTORY_DATA;

    const formatDateGroup = (date) => {
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);

      if (date.toDateString() === today.toDateString()) return "Today";
      if (date.toDateString() === yesterday.toDateString()) return "Yesterday";

      if (today.getTime() - date.getTime() < 7 * 24 * 60 * 60 * 1000) {
        return date.toLocaleDateString("en-US", { weekday: "long" }); // "Friday", "Tuesday"
      }

      return date.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    };

    const groupedData = data.reduce((acc, news) => {
      const groupKey = formatDateGroup(new Date(news.readAt));
      if (!acc[groupKey]) {
        acc[groupKey] = [];
      }
      acc[groupKey].push(news);
      return acc;
    }, {});

    setHistoryData(groupedData);
    setLoading(false);
  }, []);

  return (
    <div className="bg-white min-h-screen">
      <HeaderFeedPage userEmail={userEmail} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 font-montserrat">
        {/* Título da Página */}
        <h1 className="p-3 text-3xl font-medium text-gray-900 font-montserrat text-center">
          News History
        </h1>

        {/* Seção de Histórico */}
        <div className="space-y-12 mt-11">
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
          ) : (
            Object.keys(historyData).map((dateGroup) => (
              <section key={dateGroup}>
                {/* Título do Grupo (ex: "Friday") */}
                <h2 className="text-xl font-montserrat font-normal text-gray-900 mb-6">
                  {dateGroup}
                </h2>

                {/* Lista de Notícias no Grupo */}
                <div className="space-y-0">
                  {historyData[dateGroup].map((news) => (
                    // 3. Substituir HistoryNewsItem por NewsCard e mapear os dados
                    <NewsCard
                      key={news.id}
                      isListItem={true}
                      isLoggedIn={true} // A página de histórico é privada
                      showSaveButton={false} // Adicione esta linha para esconder o botão
                      news={{
                        ...news,
                        description: news.summary,
                        image_url: news.image,
                        published_at: news.readAt.toISOString(),
                      }}
                    />
                  ))}
                </div>
              </section>
            ))
          )}
        </div>
      </main>
    </div>
  );
};

export default NewsHistoryPage;
