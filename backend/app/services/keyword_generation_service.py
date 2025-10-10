"""
Serviço para geração inteligente de keywords para busca de notícias.
Utiliza IA (Gemini) para gerar keywords relevantes em batch.
"""

import json
import logging
from typing import Dict, List, Tuple
from app.services.ai_service import AIService
from app.utils.topic_search_cache import TopicSearchCache
from app.utils.api_rate_limiter import APIRateLimiter
from app.config.news_collection_config import get_config


class KeywordGenerationService:
    """
    Serviço responsável por:
    1. Gerar keywords para múltiplos tópicos em uma única chamada de IA
    2. Detectar idioma e país de cada tópico
    3. Construir queries booleanas com operadores OR
    """

    def __init__(
        self,
        ai_service: AIService = None,
        cache: TopicSearchCache = None,
        rate_limiter: APIRateLimiter = None,
        config: Dict = None
    ):
        """
        Inicializa o serviço de geração de keywords.

        Args:
            ai_service: Serviço de IA (se None, cria um novo)
            cache: Cache de buscas (se None, não usa cache)
            rate_limiter: Rate limiter para Gemini (se None, não usa throttling)
            config: Configurações (se None, usa padrão)
        """
        self.ai_service = ai_service or AIService()
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.config = config or get_config()

        logging.info("KeywordGenerationService inicializado")

    def generate_keywords_batch(
        self,
        topic_names: List[str]
    ) -> Dict[str, Dict]:
        """
        Gera keywords para múltiplos tópicos em uma única chamada de IA.

        Args:
            topic_names: Lista de nomes de tópicos

        Returns:
            Dicionário {topic_name: {
                "keywords": [[kw1, kw2, kw3], [kw4, kw5, kw6]],
                "language": "pt",
                "country": "br"
            }}
        """
        if not topic_names:
            logging.warning("Lista vazia de tópicos para gerar keywords")
            return {}

        logging.info(f"Gerando keywords para {len(topic_names)} tópicos em batch")

        # Preparar informações de cada tópico
        topics_info = {}
        for topic_name in topic_names:
            used_keywords = []
            if self.cache:
                used_keywords = self.cache.get_used_keywords(
                    topic_name,
                    hours=self.config["cache_ttl_hours"]
                )

            topics_info[topic_name] = {
                "used_keywords": used_keywords
            }

        # Construir prompt
        prompt = self._build_batch_prompt(topics_info)

        # Aguardar se necessário (throttling)
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        # Chamar IA
        try:
            response = self.ai_service.generate_content(prompt)

            # Registrar chamada
            if self.rate_limiter:
                self.rate_limiter.record_call()

            if not response:
                logging.error("Resposta vazia da IA para geração de keywords")
                return self._fallback_keywords(topic_names)

            # Parse da resposta
            keywords_dict = self._parse_keywords_response(response)

            # Validar e garantir formato correto
            validated = self._validate_and_fix_keywords(keywords_dict, topic_names)

            logging.info(f"Keywords geradas com sucesso para {len(validated)} tópicos")
            return validated

        except Exception as e:
            logging.error(f"Erro ao gerar keywords: {e}", exc_info=True)
            return self._fallback_keywords(topic_names)

    def _build_batch_prompt(self, topics_info: Dict[str, Dict]) -> str:
        """
        Constrói o prompt para geração de keywords em batch.

        Args:
            topics_info: {topic_name: {"used_keywords": [...]}}

        Returns:
            Prompt formatado
        """
        config = self.config
        searches_per_topic = config["searches_per_topic"]
        keywords_per_search = config["keywords_per_search"]

        prompt = f"""Gere palavras-chave para buscar notícias de cada tópico da lista e identifique o idioma/país correto.

**Regras OBRIGATÓRIAS:**
1. Para cada tópico, gere EXATAMENTE {searches_per_topic} GRUPOS de keywords
2. Cada grupo deve ter EXATAMENTE {keywords_per_search} palavras-chave ou expressões curtas (máx 3 palavras)
3. As keywords devem estar NO MESMO IDIOMA do tópico fornecido
4. Detecte o idioma do tópico e retorne o código de idioma (pt para português, en para inglês)
5. Para português, use country "br". Para inglês, use country "us"
6. Seja específico, atual e relevante (tendências, termos populares)
7. EVITE as keywords já usadas recentemente (listadas para cada tópico)
8. Varie as keywords entre os grupos para cobrir diferentes aspectos do tópico

**Formato de Saída OBRIGATÓRIO:**
Retorne APENAS um objeto JSON sem nenhum texto adicional, markdown ou formatação.
A estrutura deve ser:
{{
  "nome_do_topico": {{
    "keywords": [
      ["keyword1", "keyword2", "keyword3"],
      ["keyword4", "keyword5", "keyword6"]
    ],
    "language": "pt",
    "country": "br"
  }},
  "outro_topico": {{
    "keywords": [
      ["keyword1", "keyword2", "keyword3"]
    ],
    "language": "en",
    "country": "us"
  }}
}}

**Exemplo de Resposta Completa:**
{{
  "tecnologia": {{
    "keywords": [
      ["inteligência artificial", "IA", "machine learning"]
    ],
    "language": "pt",
    "country": "br"
  }},
  "technology": {{
    "keywords": [
      ["artificial intelligence", "AI", "innovation"]
    ],
    "language": "en",
    "country": "us"
  }}
}}

**Tópicos e keywords já usadas:**
{json.dumps(topics_info, indent=2, ensure_ascii=False)}

**Seu JSON de resposta:**"""

        return prompt

    def _parse_keywords_response(self, response: str) -> Dict[str, Dict]:
        """
        Parse da resposta da IA.

        Args:
            response: Texto de resposta da IA

        Returns:
            Dicionário parseado com keywords, language e country
        """
        # Limpar resposta (remover markdown se houver)
        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Parse JSON
        try:
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON da IA: {e}")
            logging.debug(f"Resposta recebida: {response[:500]}")
            raise

    def _validate_and_fix_keywords(
        self,
        keywords_dict: Dict[str, Dict],
        expected_topics: List[str]
    ) -> Dict[str, Dict]:
        """
        Valida e corrige o formato das keywords geradas.

        Args:
            keywords_dict: Dicionário retornado pela IA
            expected_topics: Lista de tópicos esperados

        Returns:
            Dicionário validado e corrigido com keywords, language e country
        """
        config = self.config
        searches_per_topic = config["searches_per_topic"]
        keywords_per_search = config["keywords_per_search"]

        validated = {}

        for topic_name in expected_topics:
            topic_lower = topic_name.lower()

            # Buscar no dict (case-insensitive)
            topic_data = None
            for key, value in keywords_dict.items():
                if key.lower() == topic_lower:
                    topic_data = value
                    break

            # Se não encontrou, usar fallback
            if not topic_data or not isinstance(topic_data, dict):
                logging.warning(f"IA não retornou dados para '{topic_name}'. Usando fallback.")
                lang, country = self._detect_language_fallback(topic_name)
                validated[topic_lower] = {
                    "keywords": self._fallback_keywords_for_topic(topic_name),
                    "language": lang,
                    "country": country
                }
                continue

            # Extrair keywords
            keywords_groups = topic_data.get("keywords", [])
            language = topic_data.get("language", "en")
            country = topic_data.get("country", "us")

            # Validar estrutura de keywords
            if not isinstance(keywords_groups, list):
                logging.warning(f"Formato de keywords inválido para '{topic_name}'. Usando fallback.")
                keywords_groups = self._fallback_keywords_for_topic(topic_name)

            # Garantir quantidade correta de grupos
            while len(keywords_groups) < searches_per_topic:
                keywords_groups.append([topic_name] * keywords_per_search)

            keywords_groups = keywords_groups[:searches_per_topic]

            # Validar cada grupo
            for i, group in enumerate(keywords_groups):
                if not isinstance(group, list):
                    keywords_groups[i] = [topic_name] * keywords_per_search
                    continue

                # Garantir quantidade correta de keywords
                while len(group) < keywords_per_search:
                    group.append(topic_name)

                keywords_groups[i] = group[:keywords_per_search]

            # Validar language e country
            if language not in config["supported_languages"]:
                logging.warning(f"Idioma '{language}' não suportado para '{topic_name}'. Usando fallback.")
                language, country = self._detect_language_fallback(topic_name)

            validated[topic_lower] = {
                "keywords": keywords_groups,
                "language": language,
                "country": country
            }

        return validated

    def _fallback_keywords(self, topic_names: List[str]) -> Dict[str, Dict]:
        """
        Gera keywords de fallback para todos os tópicos.

        Args:
            topic_names: Lista de tópicos

        Returns:
            Dicionário com keywords, language e country fallback
        """
        result = {}
        for topic_name in topic_names:
            lang, country = self._detect_language_fallback(topic_name)
            result[topic_name.lower()] = {
                "keywords": self._fallback_keywords_for_topic(topic_name),
                "language": lang,
                "country": country
            }
        return result

    def _fallback_keywords_for_topic(self, topic_name: str) -> List[List[str]]:
        """
        Gera keywords de fallback para um tópico.

        Args:
            topic_name: Nome do tópico

        Returns:
            Lista de grupos de keywords
        """
        config = self.config
        searches_per_topic = config["searches_per_topic"]
        keywords_per_search = config["keywords_per_search"]

        # Simplesmente repetir o nome do tópico
        return [
            [topic_name] * keywords_per_search
            for _ in range(searches_per_topic)
        ]

    def _detect_language_fallback(self, topic_name: str) -> Tuple[str, str]:
        """
        Detecta idioma e país de um tópico como fallback (quando IA falha).

        Atualmente suporta apenas PT e EN.

        Args:
            topic_name: Nome do tópico

        Returns:
            Tupla (language, country) ex: ("pt", "br")
        """
        # Caracteres específicos do português
        pt_chars = "áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ"

        if any(char in pt_chars for char in topic_name):
            return ("pt", "br")

        # Default: inglês
        return ("en", "us")

    def build_boolean_query(self, keywords: List[str]) -> str:
        """
        Constrói uma query booleana usando operador OR.

        Args:
            keywords: Lista de keywords

        Returns:
            Query formatada ex: "IA OR inteligência artificial OR machine learning"
        """
        if not keywords:
            return ""

        # Filtrar keywords vazias
        valid_keywords = [kw.strip() for kw in keywords if kw and kw.strip()]

        if not valid_keywords:
            return ""

        # Juntar com OR
        query = " OR ".join(valid_keywords)

        logging.debug(f"Query booleana construída: {query}")
        return query
