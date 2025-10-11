import logging
import json
from app.services.ai_service import AIService
from app.models.topic import Topic


class TopicSimilarityService:
    def __init__(self, ai_service: AIService | None = None):
        self.ai_service = ai_service or AIService()

    def find_similar_topics_batch(self, topic_names: list[str], existing_topics: list[Topic]) -> dict[str, Topic | None]:
        if not topic_names or len(topic_names) == 0:
            logging.warning("Lista vazia de tópicos fornecida para busca batch.")
            return {}

        if not existing_topics or len(existing_topics) == 0:
            logging.debug("Nenhum tópico existente para comparar. Todos serão criados.")
            return {name: None for name in topic_names}

        # Normalizar tópicos
        topic_names = [t.strip().lower() for t in topic_names if t and len(t.strip()) > 0]
        if not topic_names:
            return {}

        # Remover duplicatas mantendo ordem
        seen = set()
        unique_topics = []
        for t in topic_names:
            if t not in seen:
                seen.add(t)
                unique_topics.append(t)

        topic_names_list = [t.name for t in existing_topics[:100]]  # Limitar a 100

        prompt = f"""Analise cada tópico da "lista_para_verificar" e encontre o tópico mais similar semanticamente na "lista_existente".

**Regras:**
1.  **Similaridade Semântica (Critério Principal):** A correspondência deve ter um significado conceitual quase idêntico. Considere sinônimos, variações de escrita e o núcleo da ideia.
    * **EXEMPLO VÁLIDO:** "futebol nacional" -> "futebol".

2.  **Restrição Estrita de Idioma (REGRA CRÍTICA):** O mapeamento SÓ é válido se ambos os tópicos estiverem no mesmo idioma. Tópicos que são traduções diretas um do outro devem ser considerados como não similares.
    * **EXEMPLO INVÁLIDO:** O tópico "soccer" (da lista a verificar) NÃO PODE ser mapeado para "futebol" (da lista existente). O resultado deve ser `null`.

3.  **Correspondência de Escopo e Hierarquia (REGRA CRÍTICA):** A associação só pode ocorrer entre tópicos de escopo ou granularidade similares. Evite rigorosamente mapear um tópico geral (pai) para um específico (filho) ou vice-versa. Se a única correspondência semântica for hierarquicamente diferente, considere que não há um mapeamento válido.
    * **NÃO FAÇA (Específico para Geral):** "Futebol" -> "Esportes". (Futebol é um TIPO de esporte).
    * **NÃO FAÇA (Geral para Específico):** "Eleição" -> "Votação". (Votação é uma PARTE de uma eleição).
    * **FAÇA (Escopo Similar):** "Eleições Presidenciais" -> "Eleições". (Ambos tratam do mesmo conceito central com níveis de especificidade muito próximos).

4.  **Resultado Padrão (Sem Correspondência):** Se, após aplicar todas as regras acima, nenhum tópico da "lista_existente" for uma correspondência válida, o valor para o tópico em verificação deve ser `null`.

**Formato de Saída OBRIGATÓRIO:**
Sua resposta deve ser um ÚNICO objeto JSON.
As chaves devem ser os tópicos da "lista_para_verificar".
Os valores devem ser o nome do tópico similar encontrado na "lista_existente" ou `null`.
Responda APENAS com o objeto JSON, sem nenhum texto adicional ou formatação de markdown (como ```json).

**Exemplo de Resposta:**
{{
  "soccer": null,
  "política": "política",
  "saúde": "health",
  "economia global": "economia"
}}

**Listas para Análise:**

**lista_para_verificar:**
[{", ".join(f'"{t}"' for t in unique_topics)}]

**lista_existente:**
[{", ".join(f'"{t}"' for t in topic_names_list)}]

**Seu Objeto JSON de Resposta:**"""

        try:
            response = self.ai_service.generate_content(prompt)
            if not response:
                logging.warning("Resposta vazia da IA na busca batch de similaridade.")
                return {name: None for name in unique_topics}

            # Limpar e decodificar a resposta JSON
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            similarity_map = json.loads(cleaned_response)

            # Mapear nomes de tópicos para objetos Topic
            existing_topics_map = {t.name.lower(): t for t in existing_topics}
            final_result = {}

            for topic_name, similar_name in similarity_map.items():
                topic_name_lower = topic_name.lower()

                if similar_name is None:
                    final_result[topic_name_lower] = None
                    logging.debug(f"Batch: '{topic_name_lower}' → NENHUM (conforme IA)")
                else:
                    similar_name_lower = similar_name.lower()
                    # Encontrar o objeto Topic correspondente
                    similar_topic_obj = existing_topics_map.get(similar_name_lower)

                    if similar_topic_obj:
                        final_result[topic_name_lower] = similar_topic_obj
                        logging.info(f"Batch: '{topic_name_lower}' → '{similar_topic_obj.name}'")
                    else:
                        # IA alucinou um tópico que não está na lista de existentes
                        final_result[topic_name_lower] = None
                        logging.warning(f"Batch: IA indicou '{similar_name}' para '{topic_name_lower}', mas não foi encontrado na lista de existentes.")

            # Garantir que todos os tópicos originais tenham uma entrada no resultado
            for topic_name in unique_topics:
                if topic_name.lower() not in final_result:
                    final_result[topic_name.lower()] = None

            logging.info(f"Batch processado: {len(final_result)} tópicos verificados em 1 request")
            return final_result
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON da IA para similaridade: {e}", exc_info=True)
            logging.debug(f"Resposta recebida da IA: {response}")
            return {name.lower(): None for name in unique_topics}
        except Exception as e:
            logging.error(f"Erro ao buscar similaridade batch: {e}", exc_info=True)
            return {name.lower(): None for name in unique_topics}
