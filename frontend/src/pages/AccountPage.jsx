import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { usersAPI, topicsAPI, newsSourcesAPI } from "../services/api";
import { useAuthContext } from "../contexts/AuthContext";

import { motion, AnimatePresence } from "framer-motion";
import { toast } from "react-toastify";

import PreferredTopics from "../components/PreferredTopics";

const InfoRow = ({ label, value, action, actionLink }) => (
  <div className="flex justify-between items-center py-2 sm:py-3">
    <div>
      <p className="text-sm sm:text-base text-gray-500 font-montserrat">{label}</p>
      <p className="mt-1 text-sm sm:text-base text-gray-900 font-montserrat break-words">{value}</p>
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
          className="font-medium text-sm sm:text-base text-black font-montserrat"
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

const AccountPage = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newTopic, setNewTopic] = useState("");
  const [topicError, setTopicError] = useState("");
  const navigate = useNavigate();

  // Contexto de autenticação para sincronizar estado
  const { isAuthenticated, loading: authLoading, checkAuth } = useAuthContext();

  const handleOpenAddSource = () => navigate("/add-source");

  useEffect(() => {
    // Aguarda que a autenticação seja verificada antes de buscar dados
    if (authLoading) {
      return; // Aguarda AuthContext terminar verificação
    }

    if (!isAuthenticated) {
      return; // Se não autenticado, PrivateRoute já vai redirecionar
    }

    const fetchUserData = async (retryCount = 0) => {
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
        console.log("Erro ao buscar dados do usuário:", err);

        // Se for erro 401, tenta revalidar autenticação
        if (err.status === 401 || err.isAuthError) {
          console.log("Token pode ter expirado, revalidando autenticação...");
          try {
            await checkAuth();
            return; // checkAuth vai atualizar o estado, useEffect vai executar novamente
          } catch (authErr) {
            console.error("Falha ao revalidar autenticação:", authErr);
            setError("Sua sessão expirou. Você será redirecionado para fazer login.");
            return;
          }
        }

        // Para outros erros, tenta retry uma vez
        if (retryCount < 1) {
          console.log(`Tentando novamente (${retryCount + 1}/1)...`);
          setTimeout(() => fetchUserData(retryCount + 1), 1000);
          return;
        }

        setError(err.message || "Erro de conexão ao buscar dados do usuário.");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [authLoading, isAuthenticated, checkAuth]); // Executa quando autenticação muda

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
      const result = await newsSourcesAPI.detachSource(sourceId);

      if (result.success) {
        setUserData((currentUserData) => ({
          ...currentUserData,
          preferred_sources: currentUserData.preferred_sources.filter(
            (source) => source.id !== sourceId
          ),
        }));
      } else {
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

  // Aguarda autenticação e carregamento de dados
  if (authLoading || loading || !userData) return null;

  // mensagem de erro se a busca de dados falhar
  if (error) {
    return (
      <div className="flex justify-center items-center h-screen text-red-500">
        Erro: {error}
      </div>
    );
  }

  return (
    <motion.section
      className="mt-8 md:mt-16 w-full md:w-2/3 lg:w-1/2"
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
  );
};

export default AccountPage;
