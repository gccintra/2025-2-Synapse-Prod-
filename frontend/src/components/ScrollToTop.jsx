import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const ScrollToTop = () => {
  // Obtém o caminho atual da URL
  const { pathname } = useLocation();

  useEffect(() => {
    // Sempre que o 'pathname' mudar, rola suavemente para o topo
    window.scrollTo({
      top: 0,
      left: 0, // Aqui está a mágica da animação suave
    });
  }, [pathname]); // A dependência [pathname] garante que rode a cada mudança de rota

  return null; // Este componente não renderiza nada visualmente
};

export default ScrollToTop;
