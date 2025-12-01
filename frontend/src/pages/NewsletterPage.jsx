import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ConfirmationModal from "../components/ConfirmationModal";

import { usersAPI } from "../services/api";

const FAQItem = ({ question, answer, isLast }) => {
  const [isOpen, setIsOpen] = useState(false);
  const itemRef = useRef(null);

  const answerVariants = {
    hidden: { opacity: 0, height: 0, marginTop: 0 },
    visible: { opacity: 1, height: "auto", marginTop: 12 },
  };

  useEffect(() => {
    if (isOpen && isLast) {
      const timer = setTimeout(() => {
        itemRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "end",
        });
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen, isLast]);

  return (
    <div
      className={`py-5 cursor-pointer ${
        !isLast ? "border-b border-gray-200" : ""
      }`}
      onClick={() => setIsOpen(!isOpen)}
      ref={itemRef}
    >
      {/* Cabeçalho da Pergunta (Sempre visível) */}
      <div className="flex justify-between items-center select-none">
        <h4 className="mt-4 font-medium text-base text-black font-montserrat pr-10">
          {question}
        </h4>

        {/* Ícone da Seta Animada */}
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.3 }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </motion.div>
      </div>

      {/* Corpo da Resposta (Animado) */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={answerVariants}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <p className="mt-4 text-sm text-gray-600 font-montserrat leading-relaxed pr-8">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- página principal ---
const NewsletterPage = () => {
  const [isSubscribed, setIsSubscribed] = useState(null);
  const [loading, setLoading] = useState(true);

  const [modalState, setModalState] = useState({
    isOpen: false,
    title: "",
    message: "",
    onConfirm: () => {},
  });

  useEffect(() => {
    const fetchNewsletter = async () => {
      try {
        const json = await usersAPI.getUserProfile();

        if (json.success && json.data.newsletter !== undefined) {
          setIsSubscribed(json.data.newsletter);
        }
      } catch (err) {
        console.error("Erro ao carregar newsletter:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchNewsletter();
  }, []);

  const updateNewsletter = async (value) => {
    try {
      await usersAPI.changeNewsletter(value);
    } catch (err) {
      console.error("Erro ao salvar newsletter:", err);
    }
  };

  const handleSubscriptionChange = (subscribe) => {
    if (loading) return;

    setModalState({
      isOpen: true,
      title: subscribe ? "Confirm Subscription" : "Confirm Unsubscription",
      message: subscribe
        ? "Do you want to subscribe to receive our Newsletter?"
        : "Do you really want to unsubscribe from our Newsletter?",
      onConfirm: async () => {
        setIsSubscribed(subscribe);
        await updateNewsletter(subscribe);
        setModalState((prev) => ({ ...prev, isOpen: false }));
      },
    });
  };

  const closeModal = () => {
    setModalState((prev) => ({ ...prev, isOpen: false }));
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.2 } },
  };
  const sectionVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  return (
    <>
      <motion.section
        className="mt-16 w-11/12 min-[670px]:w-1/2"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* --- SEÇÃO SUBSCRIBE --- */}
        <motion.div variants={sectionVariants} className="mb-12">
          <h2 className="text-xl font-medium text-gray-900 font-montserrat mb-4">
            Subscribe
          </h2>
          <hr className="border-t-2 border-black mb-8" />

          <div className="border border-black rounded-md p-6 bg-gray-50 shadow-lg">
            {loading ? (
              <p className="text-sm font-montserrat">Loading...</p>
            ) : (
              <>
                <p className="text-[15px] font-medium font-montserrat mb-6">
              Do you want to receive a summary of all the news everyday by
              email?
                </p>

                <div className="flex gap-6">
              {/* Checkbox YES */}
                  <label className="flex items-center cursor-pointer group">
                    <div
                      className={`w-5 h-5 border border-black rounded mr-2 flex items-center justify-center transition-colors ${
                        isSubscribed === true ? "bg-black" : "bg-transparent"
                      }`}
                    >
                      {isSubscribed === true && (
                    <svg
                      className="w-3 h-3 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="3"
                        d="M5 13l4 4L19 7"
                      ></path>
                        </svg>
                      )}
                    </div>
                    <span className="text-sm font-montserrat">yes</span>
                    <input
                      type="radio"
                      name="newsletter"
                      className="hidden"
                      checked={isSubscribed === true}
                      onChange={() => handleSubscriptionChange(true)}
                    />
                  </label>

              {/* Checkbox NO */}
                  <label className="flex items-center cursor-pointer group">
                    <div
                      className={`w-5 h-5 border border-black rounded mr-2 flex items-center justify-center transition-colors ${
                        isSubscribed === false ? "bg-black" : "bg-transparent"
                      }`}
                    >
                      {isSubscribed === false && (
                    <svg
                      className="w-3 h-3 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="3"
                        d="M5 13l4 4L19 7"
                      ></path>
                        </svg>
                      )}
                    </div>
                    <span className="text-sm font-montserrat">no</span>
                    <input
                      type="radio"
                      name="newsletter"
                      className="hidden"
                      checked={isSubscribed === false}
                      onChange={() => handleSubscriptionChange(false)}
                    />
                  </label>
                </div>
              </>
            )}
          </div>
        </motion.div>

        {/* --- about --- */}
        <motion.div variants={sectionVariants}>
          <h2 className="text-xl font-medium text-gray-900 font-montserrat mb-4">
            About
          </h2>
          <hr className="border-t-2 border-black mb-2" />

          <div className="">
            <div className="space-y-3">
              <FAQItem
                question="What will I receive when I check what I want to receive?"
                answer="You will receive a consolidated email summary containing all the news from the topics you have selected."
              />
              <FAQItem
                question="How often will I receive the newsletter?"
                answer="We currently send out our curated digest once a day, every morning, ensuring you start your day fully informed without being overwhelmed."
              />
              <FAQItem
                question="Can I receive newsletters for multiple different interests?"
                answer="Yes. Our AI automatically combines all your selected interests into a single, comprehensive daily briefing."
              />
              <FAQItem
                question="How can I unsubscribe?"
                answer='We would be sad to see you go, but you can unsubscribe at any time by clicking the "no" button in "Subscribe".'
                isLast={true}
              />
            </div>
          </div>
        </motion.div>
      </motion.section>

      <ConfirmationModal
        isOpen={modalState.isOpen}
        title={modalState.title}
        message={modalState.message}
        onConfirm={modalState.onConfirm}
        onCancel={closeModal}
      />
    </>
  );
};

export default NewsletterPage;
