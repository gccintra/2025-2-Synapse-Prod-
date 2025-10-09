import React, { useState, useEffect } from "react";
import HeaderFeedPage from "../components/FeedPage/HeaderFeedPage";
import NewsCard from "../components/FeedPage/NewsCard";
import NewsCardSkeleton from "../components/FeedPage/NewsCardSkeleton";

const MOCK_NEWS_DATA = [
  {
    id: 1,
    type: "large",
    title:
      "A resposta oficial da Apple aos arranhões no iPhone 17. Entenda o caso do ScratchGate",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt...",
  },
  {
    id: 2,
    type: "medium",
    title:
      "Astrônomos detectam anã branca que engoliu mundo gelado parecido com Plutão",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt...",
  },
  {
    id: 3,
    type: "medium",
    title: "Google completa 27 anos com doodle especial",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt...",
  },
  {
    id: 4,
    type: "list",
    title: "12 filmes para acompanhar a disputa pelo Oscar 2026",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt...",
  },
  {
    id: 5,
    type: "list",
    title: "What's the big deal about AI data centres?",
    summary:
      "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt...",
  },
];

const FeedPage = () => {
  const [userData, setUserData] = useState({ email: "" });
  const [loading, setLoading] = useState(true); // Começa como true

  // Categorias (Tags)
  const categories = ["For You", "Business", "Technology", "Crypto"];
  const activeCategory = "For You";

  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      try {
        const apiUrl = import.meta.env.VITE_API_BASE_URL;
        const response = await fetch(`${apiUrl}/users/profile`, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });

        const data = await response.json();

        if (response.ok) {
          setUserData(data.data);
        } else {
          // Opcional: tratar erro, talvez redirecionar para o login
          console.error("Failed to fetch user data:", data.error);
        }
      } catch (err) {
        console.error("Connection error:", err);
      } finally {
        // Para este exemplo, vamos manter o loading como false para ver o mock
        // Em um caso real, você removeria a linha abaixo
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* 1. Header do Feed */}
      <HeaderFeedPage userEmail={userData.email} />

      {/* Main Content Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
        {/* 2. Tags de Filtro */}
        <div className="flex gap-4 mb-8">
          {categories.map((category) => (
            <button
              key={category}
              className={`flex items-center gap-3 mt-6 text-gray-900 text-xs border border-black shadow-lg pl-6 pr-6 py-1 rounded-full font-montserrat transition-all duration-300 ease-in-out hover:scale-[1.01] hover:shadow-xl hover:-translate-y-0.5 cursor-pointer ${
                category === activeCategory
                  ? "bg-black text-white [font-weight:600]"
                  : "bg-white hover:bg-gray-300 [font-weight:500]"
              }`}
            >
              {category}
            </button>
          ))}
        </div>

        {/* 3. Área Principal do Feed */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <NewsCardSkeleton type="large" />
            <NewsCardSkeleton type="medium" />
            <NewsCardSkeleton type="medium" />
          </div>
        ) : (
          <>
            {/* Grid para os 3 primeiros cards (Destaques) */}
            <div className="max-w-6xl">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 mb-12">
                {MOCK_NEWS_DATA.slice(0, 3).map((news) => (
                  <NewsCard key={news.id} news={news} />
                ))}
              </div>
            </div>

            {/* Layout em Lista para os demais (Corpo do Feed) */}
            <div className="space-y-6">
              {MOCK_NEWS_DATA.slice(3).map((news) => (
                <NewsCard key={news.id} news={news} isListItem={true} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default FeedPage;
