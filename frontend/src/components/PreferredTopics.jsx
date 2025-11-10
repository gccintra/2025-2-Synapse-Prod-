import React from "react";
import { motion, AnimatePresence } from "framer-motion";

const PreferredTopics = ({
  topics,
  newTopic,
  onNewTopicChange,
  onAddTopic,
  onDeleteTopic,
  topicError,
}) => {
  return (
    <div className="mt-6 rounded-lg">
      <h2 className="text-xl font-medium text-gray-900 font-montserrat">
        Preferred news topics
      </h2>
      <hr className="my-4 border-t-2 border-black mb-6" />
      {topicError && (
        <p className="mb-2 text-sm text-red-600 font-montserrat">
          {topicError}
        </p>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onAddTopic();
        }}
        className="flex items-end gap-4"
      >
        <input
          type="text"
          value={newTopic}
          onChange={onNewTopicChange}
          placeholder="enter a new topic..."
          className="h-11 flex-grow border border-gray-800 rounded px-2 focus:outline-none focus:ring-1 focus:ring-black text-xs font-montserrat"
        />
        <motion.button
          type="submit"
          className="h-11 flex items-center bg-black text-white text-xs font-bold px-4 rounded hover:bg-gray-800 font-montserrat"
          whileTap={{ scale: 0.95 }}
        >
          Add Topic
        </motion.button>
      </form>

      {/* Lista de tópicos existentes */}
      <div>
        <p className="mt-8 mb-3 text-lg font-medium text-gray-900 font-montserrat">
          Your topics
        </p>
        <div className="flex flex-wrap gap-2">
          <AnimatePresence>
            {topics.map((topic) => (
              <motion.div
                key={topic.id}
                layout
                initial={{ opacity: 0, y: -10, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: -10, scale: 0.8 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
                whileHover={{
                  x: 2,
                  transition: { type: "spring", stiffness: 250, damping: 10 },
                }}
                className="flex items-center gap-2 bg-white text-gray-900 text-sm font-medium border border-black shadow-lg pl-3 pr-2 py-1 rounded-full font-montserrat"
              >
                <span>{topic.name}</span>
                <button
                  onClick={() => onDeleteTopic(topic.id)}
                  className="text-red-500 hover:text-red-700 rounded-full hover:bg-gray-100 p-0.2"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4"
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
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default PreferredTopics;
