// src/hooks/useInfiniteScroll.js
import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Hook para implementar infinite scroll com paginação
 * @param {Function} fetchFunction - Função que busca os dados (deve receber page e perPage)
 * @param {Object} options - Opções do hook
 * @param {number} options.perPage - Itens por página (padrão: 10)
 * @param {Array} options.dependencies - Dependências que resetam os dados
 * @returns {Object} - Estado e funções do infinite scroll
 */
export const useInfiniteScroll = (fetchFunction, options = {}) => {
  const { perPage = 10, dependencies = [] } = options;

  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  const observer = useRef();
  const isInitialLoad = useRef(true);

  // Função para carregar mais dados
  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetchFunction(page, perPage);

      // Assumindo que a API retorna { data: { news: [...], pagination: {...} } }
      const newItems = response.data?.news || response.data || [];
      const pagination = response.data?.pagination || {};

      console.log(`Página ${page}: carregados ${newItems.length} itens, pagination:`, pagination);

      if (newItems.length === 0) {
        console.log('Nenhum item retornado, definindo hasMore = false');
        setHasMore(false);
      } else {
        setData(prevData => [...prevData, ...newItems]);
        setPage(prevPage => prevPage + 1);

        // Verificar se há mais páginas baseado na resposta da API
        if (pagination.page && pagination.pages) {
          const hasMorePages = pagination.page < pagination.pages;
          console.log(`Página atual: ${pagination.page}, Total de páginas: ${pagination.pages}, hasMore: ${hasMorePages}`);
          setHasMore(hasMorePages);
        } else if (newItems.length < perPage) {
          console.log(`Itens retornados (${newItems.length}) < per_page (${perPage}), definindo hasMore = false`);
          setHasMore(false);
        } else {
          console.log('Assumindo que há mais páginas (baseado no número de itens)');
          // Se não temos informação de paginação, assumir que há mais se retornou o número máximo
          setHasMore(true);
        }
      }
    } catch (err) {
      setError(err.message || 'Erro ao carregar dados');
      console.error('Erro no infinite scroll:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, page, perPage, loading, hasMore]);

  // Função para resetar os dados (útil quando filtros mudam)
  const reset = useCallback(() => {
    setData([]);
    setPage(1);
    setHasMore(true);
    setError(null);
    isInitialLoad.current = true;
  }, []);

  // Carregar primeira página
  useEffect(() => {
    if (isInitialLoad.current) {
      isInitialLoad.current = false;
      loadMore();
    }
  }, [loadMore]);

  // Resetar quando dependências mudarem
  useEffect(() => {
    if (!isInitialLoad.current) {
      reset();
    }
  }, dependencies);

  // Ref callback para o último elemento
  const lastElementRef = useCallback(node => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();

    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore && !loading) {
        loadMore();
      }
    }, {
      threshold: 0.1,
      rootMargin: '100px' // Carregar quando estiver 100px antes do elemento
    });

    if (node) observer.current.observe(node);
  }, [loading, hasMore, loadMore]);

  return {
    data,
    loading,
    hasMore,
    error,
    lastElementRef,
    reset,
    loadMore
  };
};