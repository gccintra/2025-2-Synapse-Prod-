import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import { usersAPI } from "../services/api";

import { toast } from "react-toastify";
import { motion, AnimatePresence } from "framer-motion";

import ArrowDownIcon from "../icons/arrow-down.svg";
import BackIcon from "../icons/back-svgrepo-com.svg";

const DynamicHeader = ({
  userEmail,
  isAuthenticated,
  showBackButton = true,
  backTo,
  backText,
  onBackClick,
}) => {
  const dropdownVariants = {
    hidden: {
      opacity: 0,
      y: -10,
      scale: 0.95,
      transition: { duration: 0.2, ease: "easeInOut" },
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: { duration: 0.2, ease: "easeInOut" },
    },
  };
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const actualBackTo = backTo || location.state?.from || "/feed";

  const actualBackText = backText || (location.state?.from ? "Back" : "Back");

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate(actualBackTo);
    }
  };
  const handleLogout = async () => {
    try {
      await usersAPI.logout();
      toast.success("Logout successful!");
    } catch (error) {
      console.error("Logout failed:", error);
      toast.error(error.message || "Logout failed. Please try again.");
    } finally {
      navigate("/login");
    }
  };

  return (
    <>
      <header className="flex justify-between items-center p-6 bg-white border-b border-gray-300 relative z-30">
        {/* lado esquerdo: botão "Back" ou espaço vazio */}
        <div className="flex items-center w-1/3">
          {location.pathname === "/feed" ? (
            <Link to="/feed" onClick={() => setDropdownOpen(false)}>
              <h1 className="text-3xl font-bold text-black font-rajdhani">
                Synapse
              </h1>
            </Link>
          ) : (
            // exibe o botão de voltar (se showBackButton for true)
            showBackButton && (
              <button
                onClick={handleBackClick}
                className="flex items-center text-gray-800 hover:text-gray-600"
              >
                <img src={BackIcon} alt="Back Icon" className="w-5 h-5 mr-2" />
                <span className="font-medium font-montserrat">
                  {actualBackText}
                </span>
              </button>
            )
          )}
        </div>

        {/* centro: logo Synapse */}
        <div className="flex justify-center w-1/3">
          {location.pathname !== "/feed" && ( // caso ñ estiver no feed, Synapse fica no centro
            <Link to="/feed" onClick={() => setDropdownOpen(false)}>
              <h1 className="text-3xl font-bold text-black font-rajdhani">
                Synapse
              </h1>
            </Link>
          )}
        </div>

        {/* lado direito: dropdown do usuário ou botões de Login/Signup */}
        <div className="relative flex justify-end w-1/3">
          {isAuthenticated ? (
            <div>
              <button
                className="flex items-center rounded-md text-gray-800 hover:text-gray-600 focus:outline-none text-base font-montserrat"
                onClick={() => setDropdownOpen((open) => !open)}
              >
                <span className="hidden min-[700px]:inline font-medium font-montserrat">
                  {userEmail}
                </span>
                <span className="inline min-[700px]:hidden font-medium font-montserrat">
                  {userEmail.split("@")[0]}
                </span>

                <img
                  src={ArrowDownIcon}
                  alt="Arrow Down Icon"
                  className="ml-2 w-4 h-4"
                />
              </button>
              <AnimatePresence>
                {dropdownOpen && (
                  <motion.div
                    variants={dropdownVariants}
                    initial="hidden"
                    animate="visible"
                    exit="hidden"
                    className="absolute right-0 mt-2 w-36 sm:w-48 bg-white rounded-md shadow-lg z-10 text-xs font-montserrat ring-1 ring-black ring-opacity-5"
                  >
                    <div className="p-1">
                      <Link
                        to="/account"
                        className="group flex w-full items-center rounded-t-md px-4 py-2 text-gray-900 transition-colors duration-100 hover:bg-black hover:text-white font-medium font-montserrat"
                        onClick={() => setDropdownOpen(false)}
                      >
                        <i className="fa-regular fa-user fa-fw mr-3 text-gray-900 group-hover:text-white"></i>
                        My Account
                      </Link>
                      <Link
                        to="/saved-news"
                        className="group flex w-full items-center rounded-sm px-4 py-2 text-gray-900 transition-colors duration-100 hover:bg-black hover:text-white font-medium font-montserrat"
                        onClick={() => setDropdownOpen(false)}
                      >
                        <i className="fa-regular fa-bookmark fa-fw mr-3 text-gray-900 group-hover:text-white"></i>
                        Saved News
                      </Link>
                      <Link
                        to="/history"
                        className="group flex w-full items-center rounded-sm px-4 py-2 text-gray-900 transition-colors duration-100 hover:bg-black hover:text-white font-medium font-montserrat"
                        onClick={() => setDropdownOpen(false)}
                      >
                        <i className="fa-solid fa-clock-rotate-left fa-fw mr-3 text-gray-900 group-hover:text-white"></i>
                        News History
                      </Link>
                    </div>
                    <div className="border-t border-gray-100"></div>
                    <div className="p-1">
                      <button
                        onClick={handleLogout}
                        className="group flex w-full items-center text-left rounded-b-md px-4 py-2 text-gray-900 transition-colors duration-100 hover:bg-black hover:text-white font-medium font-montserrat"
                      >
                        <i className="fa-solid fa-arrow-right-from-bracket fa-fw mr-3 text-gray-900 group-hover:text-white"></i>
                        Logout
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <>
              <Link
                to="/login"
                className="bg-black text-white font-bold py-2 px-4 rounded hover:bg-gray-800 transition-colors duration-200 font-montserrat text-sm"
              >
                Login
              </Link>
              <Link
                to="/registrar"
                className="ml-4 text-black border border-black font-bold py-2 px-4 rounded hover:bg-gray-100 transition-colors duration-200 font-montserrat text-sm"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </header>
      <div className="w-full h-px bg-gray-200"></div>
    </>
  );
};

export default DynamicHeader;
