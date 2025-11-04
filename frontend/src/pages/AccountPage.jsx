import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { usersAPI, topicsAPI, newsSourcesAPI } from "../services/api";

import { motion, AnimatePresence } from "framer-motion";
import { toast } from "react-toastify";

import DynamicHeader from "../components/DynamicHeader";
import PreferredTopics from "../components/PreferredTopics";
import AddSource from "../components/AddSource";

const InfoRow = ({ label, value, action, actionLink }) => (
  <div className="flex justify-between items-center py-3">
    <div>
      <p className="text-base text-gray-500 font-montserrat">{label}</p>
      <p className="mt-1 text-base text-gray-900 font-montserrat">{value}</p>
    </div>
    {action && (
      <motion.div
        className="relative"
        initial="rest"
        whileHover="hover"
        animate="rest"
      >
        <Link
          to={actionLink}
          className="font-medium text-base text-black font-montserrat"
        >
          {action}
        </Link>
        <motion.span
          className="absolute bottom-0 left-0 block h-0.5 w-full bg-black"
          variants={{ rest: { scaleX: 0 }, hover: { scaleX: 1 } }}
          transition={{ duration: 0.3 }}
          style={{ originX: 0 }}
        />
      </motion.div>
    )}
  </div>
);
// agrupando informações da conta do usuário.
const AccountInformation = ({ user }) => {
  const formattedBirthdate = user.birthdate
    ? new Date(user.birthdate).toLocaleDateString("pt-BR", { timeZone: "UTC" })
    : "Não informado";

  return (
    <div className="rounded-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-medium text-gray-900 font-montserrat">
          Account information
        </h2>
        <motion.div
          className="relative"
          initial="rest"
          whileHover="hover"
          animate="rest"
        >
          <Link to="/edit-account">Edit</Link>
          <motion.span
            className="absolute bottom-0 left-0 block h-0.5 w-full bg-black"
            variants={{ rest: { scaleX: 0 }, hover: { scaleX: 1 } }}
            transition={{ duration: 0.3 }}
            style={{ originX: 0 }}
          />
        </motion.div>
      </div>
      <hr className="my-4 border-t-2 border-black" />
      <div>
        <InfoRow label="Name" value={user.full_name} />
        <InfoRow label="Email" value={user.email} />
        <InfoRow label="Birthdate" value={formattedBirthdate} />
        <InfoRow
          label="Password"
          value="***************"
          action="Change"
          actionLink="/change-password"
        />
      </div>
    </div>
  );
};
// componente que exibe um card de uma fonte de notícia.
const SourceCard = ({ source, onDelete }) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: -20, scale: 0.9 }}
      whileHover={{ x: 5, transition: { type: "spring", stiffness: 300 } }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className="flex items-center justify-between border border-black rounded shadow-lg p-4"
    >
      <div>
        <h3 className="font-semibold text-gray-800">{source.name}</h3>
        {source.url && <p className="text-sm text-gray-500">{source.url}</p>}
      </div>
      <button
        onClick={() => onDelete(source.id)}
        className="text-red-500 hover:text-red-700 z-10"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </motion.div>
  );
};

// ler um cookie pelo nome
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

const AccountPage = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newTopic, setNewTopic] = useState("");
  const [topicError, setTopicError] = useState("");
  const [isAddingSource, setIsAddingSource] = useState(false);
  const navigate = useNavigate();

  const handleOpenAddSource = () => setIsAddingSource(true);

  const handleSaveSources = async (newSources) => {
    const apiUrl = import.meta.env.VITE_API_BASE_URL;
    const csrfToken = getCookie("csrf_access_token");

    const attachPromises = newSources.map((source) => {
      return fetch(`${apiUrl}/news_sources/attach`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-TOKEN": csrfToken,
        },
        body: JSON.stringify({ source_id: source.id }),
        credentials: "include",
      });
    });

    try {
      const responses = await Promise.all(attachPromises);
      const failedResponses = responses.filter((res) => !res.ok);

      if (failedResponses.length > 0) {
        // tratar erros individuais
        toast.error("Some sources could not be added.");
      }

      setUserData((prevData) => ({
        ...prevData,
        preferred_sources: [...prevData.preferred_sources, ...newSources],
      }));
    } catch (err) {
      toast.error("Connection error while saving sources.");
    } finally {
      setIsAddingSource(false);
    }
  };
  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      setError(null);
      try {
        // buscando dados do perfil, tópicos e fontes em paralelo
        const [profileRes, topicsRes, sourcesRes] = await Promise.all([
          usersAPI.getUserProfile(),
          topicsAPI.getPreferredTopics(),
          newsSourcesAPI.getAttachedSources(),
        ]);

        setUserData({
          full_name: profileRes.data.full_name,
          email: profileRes.data.email,
          birthdate: profileRes.data.birthdate,
          preferred_topics: topicsRes.data.topics || [],
          preferred_sources: sourcesRes.data || [],
        });
      } catch (err) {
        setError(err.message || "Erro de conexão ao buscar dados do usuário.");
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, [navigate]);

  // adicionar um novo tópico à lista.
  const handleAddTopic = async () => {
    if (newTopic.trim() === "") return;
    const limit = 10;
    if (userData.preferred_topics.length >= limit) {
      setTopicError("You can only add a maximum of " + limit + " topics.");
      return;
    }
    setTopicError("");

    try {
      const result = await topicsAPI.addPreferredTopic(newTopic.trim());

      if (
        !userData.preferred_topics.some((t) => t.id === result.data.topic.id)
      ) {
        setUserData((currentUserData) => ({
          ...currentUserData,
          preferred_topics: [
            ...currentUserData.preferred_topics,
            result.data.topic,
          ],
        }));
      }
      setNewTopic("");
      toast.success(result.message);
    } catch (err) {
      setTopicError("Connection error. Try again.");
    }
  };
  // deletar um tópico da lista pelo seu ID.
  const handleDeleteTopic = async (topicId) => {
    try {
      await topicsAPI.removePreferredTopic(topicId);

      setUserData((currentUserData) => ({
        ...currentUserData,
        preferred_topics: currentUserData.preferred_topics.filter(
          (topic) => topic.id !== topicId
        ),
      }));
      toast.success("Topic removed successfully.");
    } catch (err) {
      toast.error("Connection error when removing topic.");
    }
  };

  // Função para deletar uma fonte da lista pelo seu ID.
  const handleDeleteSource = async (sourceId) => {
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL;
      const csrfToken = getCookie("csrf_access_token");
      const response = await fetch(
        `${apiUrl}/news_sources/detach/${sourceId}`,
        {
          method: "DELETE",
          headers: { "X-CSRF-TOKEN": csrfToken },
          credentials: "include",
        }
      );

      if (response.ok) {
        setUserData((currentUserData) => ({
          ...currentUserData,
          preferred_sources: currentUserData.preferred_sources.filter(
            (source) => source.id !== sourceId
          ),
        }));
      } else {
        const result = await response.json();
        toast.error(result.error || "Could not remove source.");
      }
    } catch (err) {
      toast.error("Connection error when removing source.");
    }
  };
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
      },
    },
  };

  const sectionVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
    },
  };
  // spinner de carregamento
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <svg
          className="animate-spin h-10 w-10 text-black"
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
    );
  }

  // mensagem de erro se a busca de dados falhar
  if (error) {
    return (
      <div className="flex justify-center items-center h-screen text-red-500">
        Erro: {error}
      </div>
    );
  }
  if (isAddingSource) {
    return (
      <AddSource
        onSave={handleSaveSources}
        onBack={() => setIsAddingSource(false)}
        userEmail={userData.email}
      />
    );
  }

  return (
    <div className="bg-gray-50 min-h-screen">
      <DynamicHeader userEmail={userData.email} isAuthenticated={true} />
      <main className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col items-center min-[670px]:flex-row min-[670px]:items-start">
          <motion.aside
            className="mt-16 w-11/12 min-[670px]:w-1/3 min-[670px]:sticky min-[670px]:top-24 min-[670px]:self-start min-[670px]:ml-12"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
          >
            <div className="h-full">
              <nav>
                <ul>
                  <li>
                    <a
                      href="#"
                      className="relative block py-2 pl-4 text-base font-semibold text-black font-montserrat before:content-[''] before:absolute before:left-0 before:top-1/2 before:h-1/2 before:w-1.5 before:-translate-y-1/2 before:bg-black"
                    >
                      Account
                    </a>
                  </li>
                  <li>
                    <a
                      href="#"
                      className="block py-2 text-base text-gray-500 hover:text-black pl-4 font-montserrat"
                    >
                      Newsletter
                    </a>
                  </li>
                </ul>
              </nav>
            </div>
          </motion.aside>

          <motion.section
            className="mt-16 w-11/12 min-[670px]:w-1/2"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {/* seção 1 -> informações da Conta */}
            <motion.div variants={sectionVariants}>
              <AccountInformation user={userData} />
            </motion.div>

            {/* seção 2 -> tópicos Preferidos */}
            <motion.div variants={sectionVariants}>
              <PreferredTopics
                key={userData.email}
                topics={userData.preferred_topics}
                newTopic={newTopic}
                onNewTopicChange={(e) => {
                  setNewTopic(e.target.value);
                  if (topicError) setTopicError("");
                }}
                onAddTopic={handleAddTopic}
                onDeleteTopic={handleDeleteTopic}
                topicError={topicError}
              />
            </motion.div>

            {/* seção 3 -> fontes Preferidas */}
            <motion.div variants={sectionVariants}>
              <div className="mt-11 rounded-lg ">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-medium text-gray-900 font-montserrat">
                    Preferred news sources
                  </h2>
                </div>
                <hr className="my-4 border-t-2 border-black" />
                <div className="mt-6 mb-6">
                  <div className="flex justify-between items-center mb-4">
                    <p className="text-base font-medium text-gray-900 font-montserrat">
                      Your Sources
                    </p>
                    <motion.button
                      onClick={handleOpenAddSource}
                      className="h-11 flex items-center bg-black text-white text-xs font-bold px-4 rounded hover:bg-gray-800 font-montserrat"
                      whileTap={{ scale: 0.95 }}
                    >
                      Add Source
                    </motion.button>
                  </div>
                  <AnimatePresence>
                    <div className="mt-6 space-y-6">
                      {userData.preferred_sources.map((source) => (
                        <SourceCard
                          key={source.id}
                          source={source}
                          onDelete={handleDeleteSource}
                        />
                      ))}
                    </div>
                  </AnimatePresence>
                </div>
              </div>
            </motion.div>
          </motion.section>
        </div>
      </main>
    </div>
  );
};

export default AccountPage;
