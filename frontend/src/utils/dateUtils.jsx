// src/utils/dateUtils.jsx
import React from 'react';

/**
 * Formatar data ISO para formato brasileiro (DD/MM/AAAA)
 * @param {string|Date} date - Data no formato ISO ou objeto Date
 * @returns {string} Data formatada
 */
export const formatDate = (date) => {
  if (!date) return '';

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    if (isNaN(dateObj.getTime())) {
      return '';
    }

    return dateObj.toLocaleDateString('pt-BR');
  } catch (error) {
    console.error('Erro ao formatar data:', error);
    return '';
  }
};

/**
 * Formatar data para formato longo (DD de mês de AAAA)
 * @param {string|Date} date - Data no formato ISO ou objeto Date
 * @returns {string} Data formatada
 */
export const formatDateLong = (date) => {
  if (!date) return '';

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    if (isNaN(dateObj.getTime())) {
      return '';
    }

    return dateObj.toLocaleDateString('pt-BR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  } catch (error) {
    console.error('Erro ao formatar data:', error);
    return '';
  }
};

/**
 * Formatar data para mostrar tempo relativo (ex: "há 2 horas", "ontem")
 * @param {string|Date} date - Data no formato ISO ou objeto Date
 * @returns {string} Tempo relativo
 */
export const formatTimeAgo = (date) => {
  if (!date) return '';

  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    if (isNaN(dateObj.getTime())) {
      return '';
    }

    const now = new Date();
    const diffMs = now - dateObj;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) {
      return 'agora mesmo';
    } else if (diffMins < 60) {
      return `há ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
    } else if (diffHours < 24) {
      return `há ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
    } else if (diffDays === 1) {
      return 'ontem';
    } else if (diffDays < 7) {
      return `há ${diffDays} dia${diffDays > 1 ? 's' : ''}`;
    } else {
      return formatDate(dateObj);
    }
  } catch (error) {
    console.error('Erro ao formatar tempo relativo:', error);
    return '';
  }
};

/**
 * Componente de metadados reutilizável para exibir fonte e data
 * @param {Object} props
 * @param {string} props.sourceName - Nome da fonte
 * @param {string|Date} props.publishedAt - Data de publicação
 * @param {string} props.className - Classes CSS adicionais
 * @returns {JSX.Element}
 */
export const NewsMetadata = ({ sourceName, publishedAt, className = '', showTimeAgo = false }) => {
  const source = sourceName || 'Fonte não informada';
  const date = showTimeAgo ? formatTimeAgo(publishedAt) : formatDate(publishedAt);

  if (!date) {
    return (
      <p className={`text-gray-600 ${className}`}>
        <span className="font-semibold text-black">{source}</span>
      </p>
    );
  }

  return (
    <p className={`text-gray-600 ${className}`}>
      <span className="font-semibold text-black">{source}</span>
      {date && <span> • {date}</span>}
    </p>
  );
};