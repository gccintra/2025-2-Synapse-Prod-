import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import BackIcon from "../../icons/back-svgrepo-com.svg";

const HeaderNewsPage = () => {
  return (
    <>
      <header className="flex justify-between items-center p-6 bg-white border-b border-gray-100 relative">
        {/* Lado esquerdo: Botão "Back to feed" */}
        <Link
          to="/feed"
          className="flex items-center text-gray-800 hover:text-gray-600"
        >
          <img src={BackIcon} alt="Ícone de Voltar" className="w-5 h-5 mr-2" />
          <span className="font-medium font-montserrat">Back to feed</span>
        </Link>

        {/* Lado direito: E-mail do usuário + seta + dropdown */}
        <div className="relative">
          <h1 className="text-lg font-bold text-black font-rajdhani">
            Synapse
          </h1>
        </div>
      </header>
      <div className="w-full h-px bg-gray-200"></div>
    </>
  );
};

export default HeaderNewsPage;
