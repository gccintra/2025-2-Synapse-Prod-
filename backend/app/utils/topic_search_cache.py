"""
Sistema de cache para controlar buscas de notícias por tópico.
Evita buscar o mesmo tópico repetidamente em um curto período de tempo.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class TopicSearchCache:
    """
    Gerencia um cache de buscas de notícias por tópico.

    O cache armazena:
    - Keywords usadas em cada busca
    - Timestamp de cada busca
    - Idioma e país usados
    - Quantidade de notícias encontradas

    Estrutura do cache:
    {
        "tecnologia": {
            "searches": [
                {
                    "keywords": ["IA", "machine learning", "deep learning"],
                    "timestamp": "2025-10-10T14:00:00",
                    "language": "pt",
                    "country": "br",
                    "news_found": 8
                }
            ]
        }
    }
    """

    def __init__(self, cache_file_path: str):
        """
        Inicializa o cache.

        Args:
            cache_file_path: Caminho do arquivo JSON de cache
        """
        self.cache_file_path = cache_file_path
        self.cache_data: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Carrega o cache do disco.

        Returns:
            Dicionário com dados do cache
        """
        if not os.path.exists(self.cache_file_path):
            logging.info(f"Arquivo de cache não existe. Criando novo: {self.cache_file_path}")
            self.cache_data = {}
            return self.cache_data

        try:
            with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                self.cache_data = json.load(f)
            logging.info(f"Cache carregado com sucesso. {len(self.cache_data)} tópicos em cache.")
            return self.cache_data
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON do cache: {e}. Criando novo cache vazio.")
            self.cache_data = {}
            return self.cache_data
        except Exception as e:
            logging.error(f"Erro ao carregar cache: {e}. Criando novo cache vazio.")
            self.cache_data = {}
            return self.cache_data

    def save(self) -> None:
        """Salva o cache no disco."""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)

            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)

            logging.debug(f"Cache salvo com sucesso: {self.cache_file_path}")
        except Exception as e:
            logging.error(f"Erro ao salvar cache: {e}", exc_info=True)

    def clean_old_entries(self, hours: int = 6) -> int:
        """
        Remove entradas mais antigas que o período especificado.

        Args:
            hours: Idade máxima das entradas em horas

        Returns:
            Quantidade de entradas removidas
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        removed_count = 0

        for topic_name, topic_data in list(self.cache_data.items()):
            if "searches" not in topic_data:
                continue

            original_count = len(topic_data["searches"])

            # Filtrar buscas antigas
            topic_data["searches"] = [
                search for search in topic_data["searches"]
                if self._parse_timestamp(search.get("timestamp")) > cutoff_time
            ]

            removed = original_count - len(topic_data["searches"])
            removed_count += removed

            # Se não há mais buscas, remover o tópico do cache
            if len(topic_data["searches"]) == 0:
                del self.cache_data[topic_name]

        if removed_count > 0:
            logging.info(f"Removidas {removed_count} entradas antigas do cache (>{hours}h)")

        return removed_count

    def count_searches_in_period(self, topic_name: str, hours: int = 6) -> int:
        """
        Conta quantas buscas foram feitas para um tópico no período especificado.

        Args:
            topic_name: Nome do tópico
            hours: Período em horas

        Returns:
            Quantidade de buscas no período
        """
        topic_name = topic_name.lower()

        if topic_name not in self.cache_data:
            return 0

        cutoff_time = datetime.now() - timedelta(hours=hours)
        searches = self.cache_data[topic_name].get("searches", [])

        count = sum(
            1 for search in searches
            if self._parse_timestamp(search.get("timestamp")) > cutoff_time
        )

        return count

    def get_used_keywords(self, topic_name: str, hours: int = 6) -> List[str]:
        """
        Retorna lista de keywords já usadas para um tópico no período especificado.

        Args:
            topic_name: Nome do tópico
            hours: Período em horas

        Returns:
            Lista de keywords únicas já usadas
        """
        topic_name = topic_name.lower()

        if topic_name not in self.cache_data:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        searches = self.cache_data[topic_name].get("searches", [])

        used_keywords = set()
        for search in searches:
            timestamp = self._parse_timestamp(search.get("timestamp"))
            if timestamp > cutoff_time:
                keywords = search.get("keywords", [])
                used_keywords.update(keywords)

        return list(used_keywords)

    def record_search(
        self,
        topic_name: str,
        keywords: List[str],
        language: str,
        country: str,
        news_found: int = 0
    ) -> None:
        """
        Registra uma nova busca no cache.

        Args:
            topic_name: Nome do tópico
            keywords: Lista de keywords usadas
            language: Código do idioma (ex: 'pt', 'en')
            country: Código do país (ex: 'br', 'us')
            news_found: Quantidade de notícias encontradas
        """
        topic_name = topic_name.lower()

        if topic_name not in self.cache_data:
            self.cache_data[topic_name] = {"searches": []}

        search_entry = {
            "keywords": keywords,
            "timestamp": datetime.now().isoformat(),
            "language": language,
            "country": country,
            "news_found": news_found
        }

        self.cache_data[topic_name]["searches"].append(search_entry)

        logging.debug(
            f"Busca registrada no cache: tópico='{topic_name}', "
            f"keywords={keywords}, lang={language}, country={country}"
        )

    def can_search_topic(self, topic_name: str, max_searches: int, hours: int = 6) -> bool:
        """
        Verifica se um tópico pode ser buscado novamente.

        Args:
            topic_name: Nome do tópico
            max_searches: Máximo de buscas permitidas no período
            hours: Período em horas

        Returns:
            True se pode buscar, False se atingiu o limite
        """
        search_count = self.count_searches_in_period(topic_name, hours)
        can_search = search_count < max_searches

        if not can_search:
            logging.debug(
                f"Tópico '{topic_name}' atingiu limite de buscas "
                f"({search_count}/{max_searches} em {hours}h)"
            )

        return can_search

    def get_all_topics_in_cache(self) -> List[str]:
        """
        Retorna lista de todos os tópicos que têm entradas no cache.

        Returns:
            Lista de nomes de tópicos
        """
        return list(self.cache_data.keys())

    def get_topic_info(self, topic_name: str, hours: int = 6) -> Optional[Dict[str, Any]]:
        """
        Retorna informações sobre um tópico no cache.

        Args:
            topic_name: Nome do tópico
            hours: Período em horas

        Returns:
            Dicionário com informações ou None se não encontrado
        """
        topic_name = topic_name.lower()

        if topic_name not in self.cache_data:
            return None

        search_count = self.count_searches_in_period(topic_name, hours)
        used_keywords = self.get_used_keywords(topic_name, hours)

        return {
            "topic_name": topic_name,
            "search_count": search_count,
            "used_keywords": used_keywords,
            "total_searches_all_time": len(self.cache_data[topic_name].get("searches", []))
        }

    @staticmethod
    def _parse_timestamp(timestamp_str: Optional[str]) -> datetime:
        """
        Converte string de timestamp para datetime.

        Args:
            timestamp_str: String no formato ISO 8601

        Returns:
            Objeto datetime
        """
        if not timestamp_str:
            return datetime.min

        try:
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            logging.warning(f"Timestamp inválido: {timestamp_str}")
            return datetime.min
