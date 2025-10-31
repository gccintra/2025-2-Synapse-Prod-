import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { toast } from "react-toastify";
import ArrowDownIcon from "../icons/arrow-down.svg";
import BackIcon from "../icons/back-svgrepo-com.svg";
import { usersAPI } from "../services/api";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

const DynamicHeader = ({
  userEmail: propUserEmail,
  isAuthenticated: propIsAuthenticated,
  showBackButton = true,
  backTo,
  backText,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [localUserEmail, setLocalUserEmail] = useState(propUserEmail || "");
  const [localIsAuthenticated, setLocalIsAuthenticated] = useState(
    propIsAuthenticated !== undefined ? propIsAuthenticated : false
  );
  const navigate = useNavigate();
  const location = useLocation();

  // busca dados do usuário se não forem fornecidos via props
  useEffect(() => {
    if (!propUserEmail || propIsAuthenticated === undefined) {
      const fetchUserData = async () => {
        try {
          const response = await usersAPI.getUserProfile();
          setLocalUserEmail(response.data.email || "");
          setLocalIsAuthenticated(true);
        } catch (err) {
          console.error("Failed to fetch user data in DynamicHeader:", err);
          setLocalIsAuthenticated(false);
        }
      };
      fetchUserData();
    }
  }, [propUserEmail, propIsAuthenticated]);

  const actualBackTo = backTo || location.state?.from || "/feed";

  const actualBackText =
    backText || (location.state?.from ? "Back" : "Back to feed");

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

  const displayEmail = propUserEmail || localUserEmail;
  const displayIsAuthenticated =
    propIsAuthenticated !== undefined
      ? propIsAuthenticated
      : localIsAuthenticated;

  return (
    <>
      <header className="flex justify-between items-center p-6 bg-white border-b border-gray-300 relative">
        {/* lado esquerdo: botão "Back" ou espaço vazio */}
        <div className="flex items-center w-1/3">
          {location.pathname === "/feed" ? ( // caso esteja no feed, Synapse vai para a esquerda
            <Link to="/feed" onClick={() => setDropdownOpen(false)}>
              <h1 className="text-3xl font-bold text-black font-rajdhani">
                Synapse
              </h1>
            </Link>
          ) : (
            // exibe o botão de voltar (se showBackButton for true)
            showBackButton && (
              <button
                onClick={() => navigate(actualBackTo)}
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
          {location.pathname !== "/feed" && ( // caso NÃO estiver no feed, Synapse fica no centro
            <Link to="/feed" onClick={() => setDropdownOpen(false)}>
              <h1 className="text-3xl font-bold text-black font-rajdhani">
                Synapse
              </h1>
            </Link>
          )}
        </div>

        {/* lado direito: dropdown do usuário ou botões de Login/Signup */}
        <div className="relative flex justify-end w-1/3">
          {displayIsAuthenticated ? (
            <div>
              <button
                className="flex items-center rounded-md text-gray-800 hover:text-gray-600 focus:outline-none text-base font-montserrat"
                onClick={() => setDropdownOpen((open) => !open)}
              >
                <span className="font-medium font-montserrat">
                  {displayEmail}
                </span>
                <img
                  src={ArrowDownIcon}
                  alt="Arrow Down Icon"
                  className="ml-2 w-4 h-4"
                />
              </button>
              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-32 bg-white border border-gray-200 rounded-xl shadow-lg z-10 text-xs font-montserrat">
                  <Link
                    to="/account"
                    className="block px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
                    onClick={() => setDropdownOpen(false)}
                  >
                    My Account
                  </Link>
                  <Link
                    to="/saved-news"
                    className="block px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
                    onClick={() => setDropdownOpen(false)}
                  >
                    Saved News
                  </Link>
                  <Link
                    to="/history"
                    className="block px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
                    onClick={() => setDropdownOpen(false)}
                  >
                    News History
                  </Link>
                  <hr className="border-gray-200" />
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100 font-montserrat"
                  >
                    Logout
                  </button>
                </div>
              )}
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
