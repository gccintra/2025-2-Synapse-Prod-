import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import ArrowDownIcon from "../../icons/arrow-down.svg";

// Função auxiliar para ler um cookie pelo nome
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

const HeaderFeedPage = ({}) => {
  const { isAuthenticated } = useAuth();
  const [userEmail, setUserEmail] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  // buscar o e-mail Apenas para usuários logados.
  useEffect(() => {
    if (isAuthenticated) {
      const fetchUserData = async () => {
        try {
          const apiUrl = import.meta.env.VITE_API_BASE_URL;
          const response = await fetch(`${apiUrl}/users/profile`, {
            credentials: "include",
          });
          if (response.ok) {
            const data = await response.json();
            setUserEmail(data.data.email);
          } else {
            console.error(
              "falha na autenticação ao buscar o perfil do usuário"
            );
          }
        } catch (error) {
          console.error("Erro ao buscar dados do usuário:", error);
        }
      };
      fetchUserData();
    }
  }, [isAuthenticated]);

  // Função de logout
  const handleLogout = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL;
      const csrfToken = getCookie("csrf_access_token");

      await fetch(`${apiUrl}/users/logout`, {
        method: "POST",
        headers: { "X-CSRF-TOKEN": csrfToken },
        credentials: "include",
      });
    } finally {
      window.location.href = "/login";
    }
  };

  return (
    <>
      <header className="flex justify-between items-center p-6 bg-white border-b border-gray-300 relative">
        {/* Lado esquerdo: Synapse*/}
        <Link to="/feed" onClick={() => setDropdownOpen(false)}>
          <span>
            <h1 className="text-3xl font-bold text-black font-rajdhani">
              Synapse
            </h1>
          </span>
        </Link>

        {/* Lado direito: Dropdown */}
        <div className="relative">
          {isAuthenticated ? (
            <div>
              <button
                className="flex items-center rounded-md text-gray-800 hover:text-gray-600 focus:outline-none text-base font-montserrat"
                onClick={() => setDropdownOpen((open) => !open)}
              >
                <span className="font-medium font-montserrat">{userEmail}</span>
                <img
                  src={ArrowDownIcon}
                  alt="Ícone de Seta para Baixo"
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
            // Se não autenticado, mostrar o botão do diogo(rs) para login
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

export default HeaderFeedPage;
