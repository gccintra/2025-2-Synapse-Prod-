import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { newsSourcesAPI, usersAPI } from "../services/api";
import { toast } from "react-toastify";
import DynamicHeader from "./DynamicHeader";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}
// sub-componente que representa cada card de fonte
const SourceSelectCard = ({ source, isSelected, onToggle }) => {
  const baseClasses =
    "w-11/12 mx-auto md:w-full md:mx-0 flex items-center justify-between p-4 rounded-lg cursor-pointer transition-all duration-200 border";
  const selectedClasses =
    "bg-black border-black text-white transform scale-[1.01] shadow-md";
  const unselectedClasses =
    "bg-white border-gray-300 hover:border-black text-gray-800 hover:shadow-sm";

  return (
    <div
      className={`${baseClasses} ${
        isSelected ? selectedClasses : unselectedClasses
      }`}
      onClick={() => onToggle(source)}
    >
      <div>
        <h3 className="font-semibold text-sm md:text-base font-montserrat">
          {source.name}
        </h3>
        <p
          className={`text-xs md:text-sm ${
            isSelected ? "text-gray-200" : "text-gray-500"
          }`}
        >
          {source.url}
        </p>
      </div>
      {/* Ícone de check para a animação de seleção */}
      {isSelected && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 text-white animate-pulse" // Animação
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </div>
  );
};

const AddSource = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSources, setSelectedSources] = useState({});
  const [userData, setUserData] = useState({ email: "" });
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUnattachedSources = async () => {
      setLoading(true);
      setError(null);
      try {
        // Executa as chamadas em paralelo
        const [sourcesResponse, userProfileResponse] = await Promise.allSettled(
          [newsSourcesAPI.getUnattachedSources(), usersAPI.getUserProfile()]
        );

        // Processa a resposta das fontes
        if (
          sourcesResponse.status === "fulfilled" &&
          sourcesResponse.value.success
        ) {
          setSources(sourcesResponse.value.data || []);
        } else {
          setError(sourcesResponse.value?.error || "Failed to load sources.");
        }
        // Processa a resposta do perfil do usuário
        if (
          userProfileResponse.status === "fulfilled" &&
          userProfileResponse.value.success
        ) {
          setUserData(userProfileResponse.value.data);
          setIsAuthenticated(true);
        }
      } catch (err) {
        setError(err.message || "Connection error. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    fetchUnattachedSources();
  }, []);

  const filteredSources = sources.filter(
    (source) =>
      source.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.url.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Função para adicionar ou remover uma fonte
  const handleToggleSource = (source) => {
    setSelectedSources((prevSelected) => {
      const newSelected = { ...prevSelected };
      if (newSelected[source.id]) {
        delete newSelected[source.id]; // Remove
      } else {
        newSelected[source.id] = source; // Adiciona
      }
      return newSelected;
    });
  };

  const handleSave = () => {
    const handleSaveSources = async (newSources) => {
      const csrfToken = getCookie("csrf_access_token");

      const attachPromises = newSources.map((source) =>
        newsSourcesAPI.attachSource(source.id, csrfToken)
      );

      try {
        const responses = await Promise.all(attachPromises);
        const failedResponses = responses.filter((res) => !res.ok);

        if (failedResponses.length > 0) {
          toast.error("Some sources could not be added.");
        } else {
          toast.success("Sources added successfully!");
        }
        navigate("/account");
      } catch (err) {
        toast.error("Connection error while saving sources.");
      }
    };

    handleSaveSources(Object.values(selectedSources));
  };

  const selectedCount = Object.keys(selectedSources).length;

  return (
    <div className="bg-white min-h-screen">
      <DynamicHeader
        userEmail={userData.email}
        isAuthenticated={isAuthenticated}
        onBackClick={() => navigate("/account")}
        backText="Back to Account"
      />
      <main className="max-w-xl mx-auto py-12 px-4 w-full text-center">
        <h2 className=" mb-2 text-xl sm:text-3xl font-bold text-black font-montserrat">
          Add Preferred News Sources
        </h2>
        <p className="mt-5 mb-8 text-xs sm:text-sm text-gray-600 font-montserrat">
          Select sources you trust to personalize your feed.
        </p>

        {/* Campo de Pesquisa */}
        <div className="mb-8">
          <input
            type="text"
            placeholder="search sources (e.g., The Guardian)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-11/12 mx-auto md:w-full md:mx-0 p-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:border-black focus:ring-1 focus:ring-black text-xs font-montserrat"
          />
        </div>

        {/* Div para conter a lista de fontes com rolagem */}
        <div className="h-96 overflow-y-auto space-y-4 pl-4 pr-4 mb-24 relative">
          {loading ? (
            <div className="flex justify-center items-center h-full">
              <svg
                className="animate-spin h-8 w-8 text-black"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                />
              </svg>
            </div>
          ) : error ? (
            <div className="text-center text-red-500 mt-12">{error}</div>
          ) : filteredSources.length > 0 ? (
            filteredSources.map((source) => (
              <SourceSelectCard
                key={source.id}
                source={source}
                isSelected={!!selectedSources[source.id]}
                onToggle={handleToggleSource}
              />
            ))
          ) : searchTerm ? (
            <p className="text-center text-gray-500 mt-12">
              No sources found matching "{searchTerm}".
            </p>
          ) : (
            <p className="text-center text-gray-500 mt-12">
              All available sources have been added.
            </p>
          )}
        </div>
      </main>

      {/* footer */}
      <footer
        className="fixed bottom-0 left-0 right-4 md:right-2 md:left-0
       bg-white border-t border-gray-200 p-4 shadow-lg"
      >
        <div className="max-w-xl mx-auto flex justify-between items-center">
          <p className="text-base md:text-lg font-montserrat">
            **{selectedCount}** source(s) selected
          </p>
          <button
            onClick={handleSave}
            disabled={selectedCount === 0}
            className={`px-3 py-2 md:px-5 md:py-3 rounded-lg text-white text-xs md:text-sm font-medium md:font-bold font-montserrat transition-colors ${
              selectedCount > 0
                ? "bg-black hover:bg-gray-800"
                : "bg-gray-400 cursor-not-allowed"
            }`}
          >
            Save Sources
          </button>
        </div>
      </footer>
    </div>
  );
};

export default AddSource;
