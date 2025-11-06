"""
Serviço para geração inteligente de keywords para busca de notícias.
Utiliza IA (Gemini) para gerar keywords relevantes em batch.
"""

import json
import logging
from typing import Dict, List, Tuple
from app.services.ai_service import AIService
from app.utils.api_rate_limiter import APIRateLimiter


class KeywordGenerationService:
    def __init__(
        self,
        ai_service: AIService | None = None,
        rate_limiter: APIRateLimiter | None = None
    ):
        self.ai_service = ai_service or AIService()
        self.rate_limiter = rate_limiter

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

        # Construir prompt
        prompt = self._build_batch_prompt(topic_names)

        # Aguardar se necessário (throttling)
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        # Chamar IA com tratamento específico de timeout
        try:
            logging.info("Chamando API Gemini para geração de keywords...")
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
            error_msg = str(e).lower()

            # Verificar se é erro de timeout
            if any(timeout_keyword in error_msg for timeout_keyword in ['timeout', 'timed out', '504', 'deadline']):
                logging.warning(f"Timeout da API Gemini detectado: {e}")
                logging.info("Utilizando keywords hardcoded como fallback devido ao timeout")
            else:
                logging.error(f"Erro ao gerar keywords: {e}", exc_info=True)
                logging.info("Utilizando keywords hardcoded como fallback devido ao erro")

            return self._fallback_keywords(topic_names)

    def _build_batch_prompt(self, topic_names: List[str]) -> str:
        """
        Constrói o prompt para geração de keywords em batch.

        Args:
            topic_names: Lista de nomes de tópicos.

        Returns:
            Prompt formatado
        """
        keywords_per_topic = 5

        prompt = f"""Para cada tópico da lista, gere {keywords_per_topic} palavras-chave que APARECEM EM MANCHETES REAIS de jornais e sites de notícias.

**Regras OBRIGATÓRIAS:**
1. Use APENAS termos que jornalistas usam em manchetes (nomes de empresas, pessoas famosas, eventos populares).
2. EVITE jargão técnico, acadêmico ou termos muito específicos (ex: "ESG reporting", "Supply chain resilience").
3. PREFIRA nomes próprios: empresas (Apple, Google), pessoas (CEOs, políticos), lugares, eventos.
4. As keywords devem estar no mesmo idioma do tópico.
5. Para tópicos em português, o país é 'br'. Para inglês, o país é 'us'.
6. CADA KEYWORD DEVE TER NO MÁXIMO 4 PALAVRAS.
7. A query final (keywords separadas por OR) deve ter no máximo 200 caracteres.
8. USE APENAS LETRAS, NÚMEROS E ESPAÇOS nas keywords.
9. EVITE hífens, vírgulas, pontos ou outros caracteres especiais.

**Formato de Saída OBRIGATÓRIO:**
Retorne APENAS um objeto JSON sem nenhum texto adicional, markdown ou formatação.
A estrutura deve ser:
{{
  "nome_do_topico": {{
    "keywords": [
      "keyword1", "keyword2", "keyword3", "keyword4", "keyword5"
    ],
    "language": "pt",
    "country": "br"
  }}
}}

**Exemplo de Resposta Completa:**
{{
  "Water": {{
    "keywords": [
      "Sea", "Ocean", "Whale", "Fish"
    ],
    "language": "en",
    "country": "us"
  }}
}}

**Tópicos para gerar keywords:**
{json.dumps(topic_names, indent=2, ensure_ascii=False)}

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
        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

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
        validated = {}

        for topic_name in expected_topics:
            topic_lower = topic_name.lower()

            topic_data = None
            for key, value in keywords_dict.items():
                if key.lower() == topic_lower:
                    topic_data = value
                    break

            # Se não encontrou, usar fallback
            if not topic_data or not isinstance(topic_data, dict):
                logging.warning(f"IA não retornou dados para '{topic_name}'. Usando fallback.")
                validated[topic_lower] = {
                    "keywords": self._fallback_keywords_for_topic(topic_name),
                    "language": "en",
                    "country": "us"
                }
                continue

            keywords_groups = topic_data.get("keywords", [])
            language = topic_data.get("language", "en")
            country = topic_data.get("country", "us")

            if not isinstance(keywords_groups, list):
                logging.warning(f"Formato de keywords inválido para '{topic_name}'. Usando fallback.")
                keywords_groups = self._fallback_keywords_for_topic(topic_name)
            
   
            if any(not isinstance(kw, str) for kw in keywords_groups):
                logging.warning(f"Keywords para '{topic_name}' não são strings. Usando fallback.")
                keywords_groups = self._fallback_keywords_for_topic(topic_name)

            if language not in ["pt", "en"]:
                logging.warning(f"Idioma '{language}' não suportado para '{topic_name}'. Usando padrão.")
                language = "en"
                country = "us"

            validated[topic_lower] = {
                "keywords": keywords_groups,
                "language": language,
                "country": country
            }

        return validated

    def _fallback_keywords(self, topic_names: List[str]) -> Dict[str, Dict]:
        """
        Gera keywords de fallback para todos os tópicos usando keywords hardcoded.

        Args:
            topic_names: Lista de tópicos

        Returns:
            Dicionário com keywords hardcoded, language e country fallback
        """
        result = {}
        for topic_name in topic_names:
            result[topic_name.lower()] = {
                "keywords": self._get_hardcoded_keywords(topic_name),
                "language": "en",
                "country": "us"
            }
        return result

    def _fallback_keywords_for_topic(self, topic_name: str) -> List[str]:
        """
        Gera keywords de fallback para um tópico.

        Args:
            topic_name: Nome do tópico
        """
        # Simplesmente retorna o nome do tópico como a única keyword.
        return [topic_name]

    def _get_hardcoded_keywords(self, topic_name: str) -> List[str]:
        """
        Retorna keywords hardcoded para tópicos padrão.

        Essas são keywords populares que aparecem frequentemente em manchetes
        e garantem que sempre tenhamos resultados mesmo quando a IA falha.

        Args:
            topic_name: Nome do tópico

        Returns:
            Lista de keywords hardcoded
        """
        # Keywords simples e populares que aparecem frequentemente em manchetes reais
        hardcoded_keywords = {
            'Technology': ['AI', 'software', 'hardware'],
            'Crypto': ['Bitcoin', 'blockchain', 'NFT'],
            'Games': ['console', 'eSports', 'gameplay'],
            'Economy': ['inflation', 'GDP', 'central bank'],
            'Business': ['CEO', 'M&A', 'earnings'],
            'Health': ['disease', 'vaccine', 'hospital'],
            'Science': ['NASA', 'fossil', 'physics'],
            'Entertainment': ['movie', 'music', 'series'],
            'World': ['geopolitics', 'war', 'diplomacy']
        }

        topic_lower = topic_name.lower()

        # Retornar keywords do tópico ou keywords genéricas se não encontrado
        if topic_lower in hardcoded_keywords:
            return hardcoded_keywords[topic_lower]
        else:
            # Fallback genérico: usar o próprio nome do tópico
            return [topic_name]

    def build_boolean_query(self, keywords: List[str]) -> str:
        """
        Constrói uma query booleana usando operador OR com aspas duplas.

        IMPORTANTE: Cada keyword é envolvida em aspas duplas para que a GNews API
        trate frases multi-palavra corretamente (ex: "Apple iPhone" OR "Google AI").

        Args:
            keywords: Lista de keywords

        Returns:
            Query formatada ex: '"Apple iPhone" OR "Google AI" OR "Microsoft Windows"'
        """
        if not keywords:
            return ""

        valid_keywords = []
        for kw in keywords:
            if kw and kw.strip():
                sanitized = self._sanitize_keyword(kw.strip())
                if sanitized:  
                    quoted_keyword = f'"{sanitized}"'
                    valid_keywords.append(quoted_keyword)

        if not valid_keywords:
            return ""

        query = " OR ".join(valid_keywords)
        original_length = len(query)

        if len(query) <= 200:
            logging.debug(f"Query booleana construída ({len(query)} chars): {query}")
            return query

        logging.warning(f"Query muito longa ({original_length} chars), aplicando truncamento...")

        truncated_keywords = []
        for keyword in valid_keywords:
            test_query = " OR ".join(truncated_keywords + [keyword])
            if len(test_query) <= 200:
                truncated_keywords.append(keyword)
            else:
                break

        if not truncated_keywords:
            truncated_keywords = [valid_keywords[0]]

        final_query = " OR ".join(truncated_keywords)

        logging.warning(f"Query truncada: {original_length} → {len(final_query)} chars "
                       f"({len(valid_keywords)} → {len(truncated_keywords)} keywords)")
        logging.debug(f"Query final: {final_query}")

        return final_query

    def _sanitize_keyword(self, keyword: str) -> str:
        if not keyword:
            return ""

        sanitized = str(keyword)
        sanitized = sanitized.replace("-", " ").replace("_", " ")
        sanitized = sanitized.replace('"', '').replace("'", "")

        import re
        sanitized = re.sub(r'[^a-zA-Z0-9\s]', ' ', sanitized)
        sanitized = ' '.join(sanitized.split())

        # Limitar comprimento (GNews tem limites)
        if len(sanitized) > 100:
            sanitized = sanitized[:100].strip()

        return sanitized.strip()
