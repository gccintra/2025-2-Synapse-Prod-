# Sistema de Coleta de Notícias - Synapse

## Sumário

1. [Visão Geral](#visão-geral)
2. [Arquitetura Simplificada](#arquitetura-simplificada)
3. [Fluxo de Execução](#fluxo-de-execução)
4. [Geração de Keywords com IA](#geração-de-keywords-com-ia)
5. [Coleta de Notícias](#coleta-de-notícias)
6. [Sistema de Blacklist Automático](#sistema-de-blacklist-automático)
7. [Detecção de Duplicatas](#detecção-de-duplicatas)
8. [Rate Limiting](#rate-limiting)
9. [Esquema de Banco de Dados](#esquema-de-banco-de-dados)
10. [Consumo de APIs](#consumo-de-apis)
11. [Execução e Monitoramento](#execução-e-monitoramento)

---

## Visão Geral

O **Sistema de Coleta de Notícias** é um job automatizado que implementa uma abordagem **simplificada e eficiente** para coleta de notícias:

- **Coleta por tópicos ativos**: Busca notícias para todos os tópicos configurados no banco
- **Keywords contextuais**: Gera keywords relevantes usando IA (Google Gemini)
- **Associação direta**: Cada notícia é associada a um único tópico
- **Web scraping**: Extrai conteúdo completo quando possível
- **Deduplicação**: Evita notícias duplicadas por URL
- **Rate limiting**: Respeita limites das APIs automaticamente

### Características Principais

✅ **Simplicidade**: Fluxo direto sem complexidade desnecessária
✅ **Confiabilidade**: Menos dependências, menos pontos de falha
✅ **Performance**: Processamento eficiente com uma chamada IA por execução
✅ **Escalabilidade**: Funciona independente do número de tópicos ativos

### Execução

O job pode ser executado:

```bash
# Via script principal
python /app/backend/app/jobs/collect_news.py

# Via Docker
docker exec synapse-backend python -m app.jobs.collect_news

# Execução manual para testes
docker exec synapse-backend python /app/backend/app/jobs/collect_news.py
```

---

## Arquitetura Simplificada

O sistema atual usa uma arquitetura direta e eficiente:

```
┌─────────────────────────────────────────────────────────────┐
│                    COLLECT_NEWS.PY                          │
│                  (Entry Point Principal)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                NEWS_COLLECT_SERVICE.PY                      │
│            (collect_news_simple - Método Principal)         │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│    Topics    │  │    Keywords     │  │   GNews      │
│ (Database)   │  │   (Gemini AI)   │  │  (Search)    │
└──────────────┘  └─────────────────┘  └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│ Rate Limiter │  │  Web Scraping   │  │ Deduplication│
│  (2s delay)  │  │ (Newspaper3k)   │  │  (URL-based) │
└──────────────┘  └─────────────────┘  └──────────────┘
```

### Componentes Ativos

| Componente | Localização | Responsabilidade |
|------------|-------------|------------------|
| **NewsCollectService** | `app/services/news_collect_service.py` | Orquestra todo o processo de coleta |
| **KeywordGenerationService** | `app/services/keyword_generation_service.py` | Gera keywords com IA |
| **TopicRepository** | `app/repositories/topic_repository.py` | Busca tópicos ativos no banco |
| **NewsRepository** | `app/repositories/news_repository.py` | Salva notícias e verifica duplicatas |
| **NewsSourceRepository** | `app/repositories/news_source_repository.py` | Gerencia fontes de notícias |
| **APIRateLimiter** | `app/utils/api_rate_limiter.py` | Controla chamadas às APIs |
| **ScrapingBlacklist** | `app/utils/scraping_blacklist.py` | Blacklist automático de scraping |

### Componentes Removidos

❌ **TopicPrioritizationService** (deletado)
❌ **TopicSimilarityService** (deletado)
❌ **TopicSearchCache** (deletado)
❌ **Sistema de scoring de tópicos**
❌ **Categorização automática por IA**
❌ **Relacionamento M:N entre notícias e tópicos**

---

## Fluxo de Execução

O sistema implementa **3 etapas principais**:

```
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: Carregar Tópicos Ativos                           │
│ • TopicRepository.get_all_active()                         │
│ • Retorna lista de todos os tópicos ativos do banco        │
│ • Sem limite ou priorização                                │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: Gerar Keywords em Batch (1 CHAMADA GEMINI)       │
│ • KeywordGenerationService.generate_batch()                │
│ • Envia TODOS os tópicos para IA em uma única chamada      │
│ • IA retorna keywords otimizadas para cada tópico          │
│ • Total: 1 chamada à API do Gemini por execução           │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 3: Coletar e Processar por Tópico                   │
│ • Para cada tópico ativo:                                  │
│   - Buscar artigos no GNews com keywords geradas          │
│   - Verificar duplicatas por URL                          │
│   - Fazer web scraping do conteúdo                        │
│   - Salvar diretamente com topic_id                       │
│ • Total: N chamadas GNews (N = número de tópicos ativos)  │
└─────────────────────────────────────────────────────────────┘
```

### Detalhamento do Processo

#### 1. Carregamento de Tópicos
```python
active_topics = self.topic_repo.get_all_active()
# Busca TODOS os tópicos com status ativo
# Sem priorização ou limite de quantidade
```

#### 2. Geração de Keywords
```python
keywords_map = self.keyword_service.generate_batch(
    [topic.name for topic in active_topics]
)
# Uma única chamada Gemini para todos os tópicos
# Retorna dicionário {topic_name: keywords_string}
```

#### 3. Coleta por Tópico
```python
for topic in active_topics:
    keywords = keywords_map.get(topic.name, topic.name)
    articles = self.search_articles_via_gnews(keywords)

    for article in articles:
        if not self.news_repo.find_by_url(article['url']):
            # Scraping + Salvamento + Associação direta
            news = self.create_news_from_article(article, topic.id)
            self.news_repo.create(news)
```

---

## Geração de Keywords com IA

### Estratégia de Batch Processing

O sistema otimiza o uso da API Gemini gerando keywords para **todos os tópicos em uma única chamada**:

```python
def generate_batch(self, topic_names: List[str]) -> Dict[str, str]:
    """
    Gera keywords para múltiplos tópicos em uma única chamada IA.

    Args:
        topic_names: Lista de nomes de tópicos

    Returns:
        Dicionário mapeando tópico para keywords
    """
```

### Prompt Engineering

O prompt utilizado é otimizado para gerar keywords relevantes e específicas:

```
Para cada tópico fornecido, gere 3-5 keywords/frases em inglês que sejam:
- Específicas e atuais
- Relevantes para notícias recentes
- Otimizadas para busca em APIs de notícias

Formato de resposta:
technology: "Apple iPhone" OR "Google AI" OR "Microsoft Windows"
politics: "Joe Biden" OR "Donald Trump" OR "US Congress"
...
```

### Cache e Otimização

- **Uma chamada por execução**: Independente do número de tópicos
- **Timeout configurável**: 60 segundos para evitar travamentos
- **Fallback automático**: Em caso de erro, usa nome do tópico como keyword

---

## Coleta de Notícias

### Estratégia de Busca

O sistema utiliza **GNews API** para buscar notícias por tópico:

#### Configuração de Busca
```python
search_params = {
    'q': keywords,           # Keywords geradas pela IA
    'lang': 'en',           # Inglês fixo
    'country': 'us',        # Estados Unidos fixo
    'max': 10,              # Máximo 10 artigos por tópico
}
```

#### Rate Limiting
- **Delay fixo**: 2 segundos entre chamadas
- **Retry automático**: Para erros 429 (rate limit)
- **Blacklist dinâmica**: Domínios problemáticos são bloqueados

#### Exemplo de Execução
```
8 tópicos ativos = 8 chamadas GNews
Rate limiting: 2s × 8 = 16 segundos mínimos de espera
Total estimado: 2-3 minutos por execução completa
```

---

## Sistema de Blacklist Automático

### Funcionamento

O sistema mantém uma blacklist dinâmica de domínios que apresentam problemas no scraping:

```json
{
  "blocked_domains": {
    "bloomberg.com": {
      "reason": "403 Forbidden",
      "blocked_at": "2025-10-21T02:34:22.095Z",
      "attempts": 3
    },
    "nytimes.com": {
      "reason": "403 Forbidden",
      "blocked_at": "2025-10-21T02:36:06.607Z",
      "attempts": 5
    }
  }
}
```

### Critérios de Bloqueio

Domínios são automaticamente bloqueados por:
- **SSL Errors**: Certificados inválidos
- **403 Forbidden**: Proteção anti-bot
- **Timeout**: Resposta muito lenta (>30s)
- **Rate Limiting**: Muitas tentativas consecutivas

### Localização

- **Arquivo**: `/tmp/scraping_blacklist.json`
- **Gerenciamento**: `app/utils/scraping_blacklist.py`
- **Auto-atualização**: Durante cada execução

---

## Detecção de Duplicatas

### Método Atual: URL-based

O sistema implementa detecção de duplicatas baseada em **URLs únicas**:

```python
def find_by_url(self, url: str) -> News | None:
    """
    Verifica se notícia já existe no banco por URL.

    Implementa:
    1. Busca exata por URL
    2. Normalização de URL (remove www, trailing slashes, query params)
    3. Comparação com todas as URLs existentes
    """
```

### Normalização de URL

Para evitar duplicatas por variações de URL:

```python
def _normalize_url(self, url: str) -> str:
    """
    Normaliza URL para comparação:
    - Lowercase
    - Remove 'www.'
    - Remove trailing slashes
    - Remove query parameters
    """
```

### Limitações Conhecidas

⚠️ **Duplicatas por título similar**: Sites republicam mesmo conteúdo com URLs diferentes
⚠️ **Notícias idênticas de fontes diferentes**: Mesmo título, mesma notícia, URLs únicas

### Exemplo de Duplicatas Detectadas nos Logs

```
2025-10-21 02:33:41,111 - INFO -     Notícia salva: 'Zelenskyy says his meeting with Trump was 'positiv...' → WIS10
2025-10-21 02:33:42,129 - INFO -     Notícia salva: 'Zelenskyy says his meeting with Trump was 'positiv...' → WEAU
2025-10-21 02:33:43,115 - INFO -     Notícia salva: 'Zelenskyy says his meeting with Trump was 'positiv...' → Live 5 News
```

**Status**: Sistema salva todas (URLs diferentes), mas são efetivamente duplicatas.

---

## Rate Limiting

### GNews API

```python
class APIRateLimiter:
    """
    Controla chamadas para evitar rate limiting.
    """

    @staticmethod
    def wait_if_needed():
        """Aguarda 2 segundos entre chamadas."""
        time.sleep(2)
```

### Retry Logic

```python
def search_articles_via_gnews(self, query: str) -> List[dict]:
    """
    Busca artigos com retry automático para erro 429.
    """
    try:
        return self.gnews.search(query)
    except Exception as e:
        if "429" in str(e):
            time.sleep(10)  # Aguarda mais tempo
            return self.gnews.search(query)  # Retry
        raise
```

### Limites Observados

- **GNews**: 100 requests/day (raramente atingido)
- **Gemini**: 200 requests/day (1 request por execução)
- **Scraping**: Sem limite, mas domains podem bloquear

---

## Esquema de Banco de Dados

### Estrutura Simplificada

O sistema atual usa **relacionamentos diretos 1:N**:

```sql
-- Tabela principal de notícias
CREATE TABLE news (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    url VARCHAR(500) UNIQUE NOT NULL,  -- UNIQUE constraint
    image_url VARCHAR(500),
    content TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    source_id INTEGER REFERENCES news_sources(id),
    topic_id INTEGER REFERENCES topics(id),  -- 1:N relationship
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de tópicos
CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela de fontes
CREATE TABLE news_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Relacionamentos

```
News (1) ←→ (N) Topic       # Um tópico pode ter muitas notícias
News (1) ←→ (N) NewsSource  # Uma fonte pode ter muitas notícias
```

### Tabelas Removidas

❌ `news_topics` (Many-to-Many entre news e topics)
❌ `topic_stats` (Estatísticas de tópicos)
❌ `user_news` (Relacionamento usuário-notícia)
❌ `user_topics` (Preferências de tópicos por usuário)

---

## Consumo de APIs

### Por Execução

| API | Chamadas | Uso do Limite | Observações |
|-----|----------|---------------|-------------|
| **GNews** | N (N = tópicos ativos) | ~8% do limite diário | 8 tópicos = 8 calls |
| **Gemini** | 1 | 0.5% do limite diário | Batch processing |

### Exemplo Real (8 tópicos ativos)

```
GNews API:  8 calls de ~100/day = 8%
Gemini AI:  1 call de ~200/day = 0.5%
```

### Otimizações

✅ **Batch processing**: Uma chamada Gemini para todos os tópicos
✅ **Rate limiting**: Previne bloqueios por excesso
✅ **Retry logic**: Tenta novamente em caso de erro temporário
✅ **Blacklist**: Evita tentar scraping de sites problemáticos

---

## Execução e Monitoramento

### Logs Detalhados

O sistema produz logs estruturados para monitoramento:

```
2025-10-21 02:33:04,085 - INFO - JOB DE COLETA SIMPLIFICADA INICIADO
2025-10-21 02:33:04,085 - INFO - Encontrados 8 tópicos ativos: ['technology', 'politics', ...]
2025-10-21 02:33:15,203 - INFO - Keywords geradas para 8 tópicos
2025-10-21 02:33:17,935 - INFO -   [1/8] Buscando notícias para o tópico: 'technology' (ID=1)
...
2025-10-21 02:36:31,917 - INFO - RESUMO:
2025-10-21 02:36:31,917 - INFO -   - Tópicos processados: 8 (do banco de dados)
2025-10-21 02:36:31,917 - INFO -   - Chamadas GNews: 8
2025-10-21 02:36:31,917 - INFO -   - Artigos coletados: 80
2025-10-21 02:36:31,917 - INFO -   - Novos artigos salvos: 57
2025-10-21 02:36:31,917 - INFO -   - Novas fontes: 13
```

### Métricas de Performance

#### Execução Típica (8 tópicos):
- **Tempo total**: ~3 minutos
- **Artigos coletados**: 80 (10 por tópico)
- **Taxa de sucesso**: ~71% (57/80 salvos)
- **Novas fontes**: ~13 por execução

#### Principais Causas de Falha:
1. **SSL Errors**: Certificados inválidos
2. **403 Forbidden**: Proteção anti-scraping
3. **Timeouts**: Sites muito lentos
4. **Duplicatas**: URLs já existentes no banco

### Monitoramento Recomendado

1. **Taxa de sucesso**: > 60% de artigos salvos
2. **Tempo de execução**: < 5 minutos
3. **Erros de API**: < 5% das chamadas
4. **Crescimento da blacklist**: Monitorar domínios bloqueados

---

## Considerações Finais

### Vantagens do Sistema Atual

✅ **Simplicidade**: Fácil de entender e manter
✅ **Confiabilidade**: Menos componentes = menos falhas
✅ **Eficiência**: Uma chamada IA por execução
✅ **Escalabilidade**: Funciona com qualquer número de tópicos
✅ **Transparência**: Logs detalhados para debugging

### Limitações Conhecidas

⚠️ **Duplicatas por título**: Múltiplas fontes, mesmo conteúdo
⚠️ **Sem priorização**: Todos os tópicos têm mesma importância
⚠️ **Sem categorização automática**: Associação manual a tópicos
⚠️ **Dependência de GNews**: Única fonte de descoberta de notícias

### Possíveis Melhorias Futuras

1. **Detecção de similaridade de títulos**: Evitar duplicatas semânticas
2. **Múltiplas fontes**: Integrar RSS feeds, APIs adicionais
3. **Priorização dinâmica**: Baseada em engajamento dos usuários
4. **Categorização híbrida**: IA para sugerir, humano para aprovar

---

**Última atualização**: 2025-10-21
**Versão do sistema**: Coleta Simplificada v2.0