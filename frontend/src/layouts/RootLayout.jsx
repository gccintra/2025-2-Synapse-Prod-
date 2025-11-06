import React from "react";
import { Outlet } from "react-router-dom";
import ScrollToTop from "../components/ScrollToTop"; // Importe o componente que criamos antes

const RootLayout = () => {
  return (
    <>
      {/* Este componente roda a cada mudança de rota */}
      <ScrollToTop />

      {/* O Outlet renderiza a página atual (FeedPage, NewsPage, etc.) */}
      <Outlet />
    </>
  );
};

export default RootLayout;
