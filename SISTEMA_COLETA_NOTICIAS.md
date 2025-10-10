# Sistema de Coleta Inteligente de Notícias - Synapse

## Sumário

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Fluxo de Execução](#fluxo-de-execução)
4. [Algoritmo de Priorização de Tópicos](#algoritmo-de-priorização-de-tópicos)
5. [Sistema de Cache](#sistema-de-cache)
6. [Geração Inteligente de Keywords](#geração-inteligente-de-keywords)
7. [Rate Limiting (Controle de APIs)](#rate-limiting-controle-de-apis)
8. [Coleta de Notícias](#coleta-de-notícias)
9. [Sistema de Blacklist Automático](#sistema-de-blacklist-automático)
10. [Categorização Automática](#categorização-automática)
11. [Detecção de Similaridade](#detecção-de-similaridade)
12. [Configurações](#configurações)
13. [Métricas e Monitoramento](#métricas-e-monitoramento)

---

## Visão Geral

O **Sistema de Coleta Inteligente de Notícias** é um job automatizado que:

- **Seleciona automaticamente** os melhores tópicos para buscar notícias
- **Gera keywords contextuais** usando Inteligência Artificial (Google Gemini)
- **Coleta notícias** de múltiplas fontes via GNews API
- **Extrai conteúdo completo** através de web scraping
- **Categoriza automaticamente** todas as notícias usando IA
- **Evita duplicação** de tópicos e notícias
- **Respeita limites de APIs** com throttling rigoroso

### Problema que Resolve

Sem este sistema, seria necessário:
- Escolher manualmente quais tópicos buscar
- Criar keywords para cada busca
- Lidar com duplicatas e spam
- Gerenciar limites de API manualmente
- Categorizar notícias uma a uma

O sistema faz tudo isso **automaticamente, de forma inteligente e otimizada**.

### Execução

O job roda **a cada 6 horas** via cron (configurado em `backend/crontab`):

```cron
0 */6 * * * root python -m app.jobs.collect_news
```

Você também pode executar manualmente:

```bash
docker exec synapse-cron python /app/app/jobs/collect_news.py
```

---

## Arquitetura do Sistema

O sistema é composto por diversos módulos especializados:

```
┌─────────────────────────────────────────────────────────────┐
│                    COLLECT_NEWS.PY                          │
│                  (Orquestrador Principal)                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEWS_SERVICE.PY                          │
│            (Coordena todo o processo de coleta)             │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│ Priorização  │  │    Keywords     │  │ Categorização│
│  de Tópicos  │  │   (Gemini AI)   │  │  (Gemini AI) │
└──────────────┘  └─────────────────┘  └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│    Cache     │  │  Rate Limiter   │  │ Similaridade │
│  (Histórico) │  │   (Throttle)    │  │  de Tópicos  │
└──────────────┘  └─────────────────┘  └──────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │     GNews API       │
                │   (100 req/dia)     │
                └─────────────────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Web Scraping      │
                │   (Newspaper3k)     │
                └─────────────────────┘
```

### Componentes Principais

| Componente | Localização | Responsabilidade |
|------------|-------------|------------------|
| **NewsService** | `app/services/news_service.py` | Orquestra todo o processo |
| **TopicPrioritizationService** | `app/services/topic_prioritization_service.py` | Calcula scores e prioriza tópicos |
| **KeywordGenerationService** | `app/services/keyword_generation_service.py` | Gera keywords com IA |
| **TopicSimilarityService** | `app/services/topic_similarity_service.py` | Detecta tópicos similares |
| **TopicSearchCache** | `app/utils/topic_search_cache.py` | Gerencia cache de buscas |
| **APIRateLimiter** | `app/utils/api_rate_limiter.py` | Controla chamadas às APIs |
| **ScrapingBlacklist** | `app/utils/scraping_blacklist.py` | Blacklist automático de scraping |
| **TopicStatsRepository** | `app/repositories/topic_stats_repository.py` | Consulta métricas do banco |

---

## Fluxo de Execução

O job segue **8 etapas sequenciais**:

```
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 1: Carregar Cache                                     │
│ • Carrega histórico de buscas do arquivo JSON               │
│ • Remove entradas antigas (>6 horas)                        │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 2: Priorizar Tópicos                                  │
│ • Consulta banco de dados (usuários + notícias)            │
│ • Calcula score de cada tópico                              │
│ • Seleciona os 4 tópicos mais prioritários                  │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 3: Gerar Keywords (1 CHAMADA GEMINI)                 │
│ • Envia todos os 4 tópicos para IA em BATCH                │
│ • IA retorna keywords + idioma + país para cada tópico     │
│ • Total: ~1 única chamada à API do Gemini                  │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 4: Coletar Notícias do GNews                         │
│ • 1 chamada top-headlines (obrigatória)                    │
│ • 4 chamadas search (1 por tópico prioritário)             │
│ • Total: 5 chamadas GNews API                              │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 5: Processar Notícias                                │
│ • Verifica duplicatas (URL)                                │
│ • Cria ou busca fontes no banco                            │
│ • Faz web scraping do conteúdo completo                    │
│ • Salva notícias no banco de dados                         │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 6: Categorizar em Batch (~2 CHAMADAS GEMINI)         │
│ • Extrai tópicos de todas as notícias (1 chamada)          │
│ • Verifica similaridade de tópicos (1 chamada)             │
│ • Cria novos tópicos se necessário                         │
│ • Associa notícias aos tópicos corretos                    │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 7: Salvar Cache                                       │
│ • Atualiza arquivo JSON com novas buscas                   │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ ETAPA 8: Resumo e Logs                                      │
│ • Exibe estatísticas da execução                           │
│ • Registra métricas no log                                 │
└─────────────────────────────────────────────────────────────┘
```

### Consumo de APIs

Por execução do job:
- **GNews API**: 5 chamadas (1% do limite diário de 100)
- **Gemini AI**: ~3 chamadas (1.5% do limite diário de 200)

---

## Algoritmo de Priorização de Tópicos

**Objetivo**: Selecionar os tópicos mais relevantes para buscar notícias, equilibrando demanda dos usuários e oferta de conteúdo.

### 1. Coleta de Métricas

O sistema consulta o banco de dados e coleta para cada tópico:

- **user_count**: Quantos usuários selecionaram este tópico em suas preferências
- **news_count_7d**: Quantas notícias deste tópico foram coletadas nos últimos 7 dias
- **searches_6h**: Quantas vezes este tópico foi buscado nas últimas 6 horas (do cache)

**Consulta SQL Simplificada**:
```sql
SELECT
  t.id,
  t.name,
  COUNT(DISTINCT ut.user_id) as user_count,
  COUNT(DISTINCT n.id) as news_count_7d
FROM topics t
LEFT JOIN user_topics ut ON t.id = ut.topic_id
LEFT JOIN news_topics nt ON t.id = nt.topic_id
LEFT JOIN news n ON nt.news_id = n.id
  AND n.created_at > NOW() - INTERVAL '7 days'
GROUP BY t.id, t.name
```

### 2. Cálculo do Score

Para cada tópico, o score é calculado pela fórmula:

```
score = (user_count × 10) - (news_count_7d × 0.5) + bônus_diversidade - penalidade_cache
```

Onde:
- **Demanda** (`user_count × 10`): Quanto mais usuários interessados, maior o score
- **Oferta** (`news_count_7d × 0.5`): Quanto mais notícias recentes, menor o score (evita saturação)
- **Bônus de Diversidade** (`+50`): Se nunca foi buscado nas últimas 6h
- **Penalidade de Cache** (`searches_6h × 30`): Reduz score para tópicos buscados recentemente

### 3. Bloqueio por Excesso

Tópicos com **3 ou mais buscas nas últimas 6 horas** são **bloqueados** (score = -999999).

Isso evita spam e distribui melhor as chamadas de API.

### 4. Exemplo Prático

**Cenário**:
- Tópico "tecnologia": 50 usuários, 20 notícias (7d), 0 buscas (6h)
- Tópico "política": 30 usuários, 5 notícias (7d), 2 buscas (6h)
- Tópico "esportes": 20 usuários, 30 notícias (7d), 3 buscas (6h)

**Cálculos**:

```
tecnologia:
  score = (50 × 10) - (20 × 0.5) + 50 - (0 × 30)
  score = 500 - 10 + 50 - 0 = 540

política:
  score = (30 × 10) - (5 × 0.5) + 0 - (2 × 30)
  score = 300 - 2.5 + 0 - 60 = 237.5

esportes:
  score = BLOQUEADO (3 buscas ≥ 3)
  score = -999999
```

**Ordem de Prioridade**: tecnologia (540) > política (237.5) > esportes (bloqueado)

### 5. Código de Referência

Arquivo: `backend/app/services/topic_prioritization_service.py:142-207`

```python
def _calculate_scores(self, metrics_list: List[TopicMetrics]) -> List[TopicScore]:
    for metrics in metrics_list:
        # Contar buscas no cache
        searches_6h = self.cache.count_searches_in_period(
            metrics.topic_name,
            hours=config["cache_ttl_hours"]
        )

        # Verificar bloqueio
        is_blocked = searches_6h >= config["max_searches_per_topic_in_6h"]

        # Calcular score base
        base_score = (
            metrics.user_count * config["score_user_weight"]
            - metrics.news_count_7d * config["score_news_weight"]
        )

        # Bônus de diversidade
        diversity_bonus = config["score_diversity_bonus"] if searches_6h == 0 else 0

        # Penalidade de cache
        cache_penalty = searches_6h * config["score_cache_penalty"]

        # Score final
        if is_blocked:
            final_score = -999999
        else:
            final_score = base_score + diversity_bonus - cache_penalty
```

---

## Sistema de Cache

**Objetivo**: Evitar buscar o mesmo tópico repetidamente em um curto período, otimizando o uso de APIs.

### Estrutura do Cache

O cache é armazenado em JSON (`backend/app/data/topic_search_cache.json`):

```json
{
  "tecnologia": {
    "searches": [
      {
        "keywords": ["inteligência artificial", "IA", "machine learning"],
        "timestamp": "2025-10-10T08:00:00",
        "language": "pt",
        "country": "br",
        "news_found": 8
      },
      {
        "keywords": ["blockchain", "criptomoedas", "bitcoin"],
        "timestamp": "2025-10-10T14:00:00",
        "language": "pt",
        "country": "br",
        "news_found": 5
      }
    ]
  }
}
```

### Funcionalidades

#### 1. Registro de Buscas

Cada vez que uma busca é feita, ela é registrada:

```python
cache.record_search(
    topic_name="tecnologia",
    keywords=["IA", "machine learning", "deep learning"],
    language="pt",
    country="br",
    news_found=8
)
```

#### 2. Contagem de Buscas Recentes

Conta quantas vezes um tópico foi buscado nas últimas N horas:

```python
count = cache.count_searches_in_period(
    topic_name="tecnologia",
    hours=6
)
# Retorna: 2 (se houve 2 buscas nas últimas 6h)
```

#### 3. Keywords Já Usadas

Retorna lista de keywords já utilizadas recentemente:

```python
used = cache.get_used_keywords(
    topic_name="tecnologia",
    hours=6
)
# Retorna: ["inteligência artificial", "IA", "machine learning",
#           "blockchain", "criptomoedas", "bitcoin"]
```

Isso permite que a IA evite repetir as mesmas keywords!

#### 4. Limpeza Automática

Entradas antigas (>6 horas) são removidas automaticamente:

```python
removed = cache.clean_old_entries(hours=6)
# Remove buscas com timestamp anterior a 6 horas atrás
```

### Fluxo no Job

```
┌──────────────────────┐
│ Início do Job        │
└──────────────────────┘
          ▼
┌──────────────────────┐
│ cache.load()         │ ← Carrega do arquivo JSON
└──────────────────────┘
          ▼
┌──────────────────────┐
│ clean_old_entries()  │ ← Remove entradas antigas
└──────────────────────┘
          ▼
┌──────────────────────┐
│ Priorização usa      │
│ count_searches()     │ ← Verifica histórico
└──────────────────────┘
          ▼
┌──────────────────────┐
│ Keywords usa         │
│ get_used_keywords()  │ ← Evita repetir keywords
└──────────────────────┘
          ▼
┌──────────────────────┐
│ Após cada busca:     │
│ record_search()      │ ← Registra nova busca
└──────────────────────┘
          ▼
┌──────────────────────┐
│ cache.save()         │ ← Salva no arquivo JSON
└──────────────────────┘
          ▼
┌──────────────────────┐
│ Fim do Job           │
└──────────────────────┘
```

---

## Geração Inteligente de Keywords

**Objetivo**: Usar IA (Google Gemini) para gerar keywords relevantes e contextuais para buscar notícias.

### Por Que Usar IA?

Keywords manuais ou genéricas resultam em:
- Notícias irrelevantes ou repetitivas
- Baixa diversidade de conteúdo
- Resultados desatualizados

A IA gera keywords:
- **Contextuais**: Relacionadas a tendências atuais
- **Diversificadas**: Diferentes ângulos do mesmo tópico
- **No idioma correto**: Detecta automaticamente PT, EN, etc.

### Processo em Batch

O sistema gera keywords para **TODOS os tópicos em uma única chamada de IA**!

**Exemplo de Prompt Enviado**:

```
Gere palavras-chave para buscar notícias de cada tópico da lista e identifique o idioma/país correto.

Regras:
1. Para cada tópico, gere EXATAMENTE 1 GRUPO de keywords
2. Cada grupo deve ter EXATAMENTE 5 palavras-chave
3. As keywords devem estar NO MESMO IDIOMA do tópico
4. Detecte o idioma e retorne o código (pt para português, en para inglês)
5. EVITE as keywords já usadas recentemente

Tópicos e keywords já usadas:
{
  "tecnologia": {
    "used_keywords": ["inteligência artificial", "IA", "machine learning"]
  },
  "política": {
    "used_keywords": []
  },
  "economia": {
    "used_keywords": ["inflação", "juros"]
  },
  "technology": {
    "used_keywords": []
  }
}

Formato de Saída (JSON):
{
  "tecnologia": {
    "keywords": [
      ["blockchain", "criptomoedas", "web3", "NFT", "metaverso"]
    ],
    "language": "pt",
    "country": "br"
  },
  "política": {
    "keywords": [
      ["eleições", "congresso", "reforma", "governo", "votação"]
    ],
    "language": "pt",
    "country": "br"
  },
  "economia": {
    "keywords": [
      ["PIB", "mercado", "bolsa", "investimentos", "dólar"]
    ],
    "language": "pt",
    "country": "br"
  },
  "technology": {
    "keywords": [
      ["artificial intelligence", "AI", "innovation", "startups", "tech trends"]
    ],
    "language": "en",
    "country": "us"
  }
}
```

### Resposta da IA

A IA retorna JSON estruturado com:
- **keywords**: Lista de listas (cada lista = 1 grupo de keywords)
- **language**: Código do idioma (pt, en)
- **country**: Código do país (br, us)

### Construção de Queries Booleanas

As keywords são convertidas em queries com **operador OR**:

```python
keywords = ["blockchain", "criptomoedas", "web3", "NFT", "metaverso"]
query = build_boolean_query(keywords)
# Resultado: "blockchain OR criptomoedas OR web3 OR NFT OR metaverso"
```

Esta query é enviada para a GNews API:

```
GET https://gnews.io/api/v4/search?q=blockchain OR criptomoedas OR web3 OR NFT OR metaverso&lang=pt&country=br
```

### Validação e Fallback

Se a IA falhar ou retornar formato inválido:

1. **Detecta idioma** por caracteres (ç, á, ã → português)
2. **Usa o próprio nome do tópico** como keyword
3. **Define idioma/país padrão** (en/us)

```python
# Fallback para "tecnologia"
{
  "tecnologia": {
    "keywords": [["tecnologia", "tecnologia", "tecnologia", "tecnologia", "tecnologia"]],
    "language": "pt",
    "country": "br"
  }
}
```

### Código de Referência

Arquivo: `backend/app/services/keyword_generation_service.py:46-113`

---

## Rate Limiting (Controle de APIs)

**Objetivo**: Respeitar rigorosamente os limites das APIs externas, evitando bloqueios.

### Limites das APIs

| API | Limite | Controlado Por |
|-----|--------|----------------|
| **GNews** | 100 chamadas/dia | Manual (configuração) |
| **Google Gemini** | 10 chamadas/minuto<br>200 chamadas/dia | APIRateLimiter |

### Como Funciona o Rate Limiter

O `APIRateLimiter` implementa um **algoritmo de janela deslizante**:

```
Janela de 60 segundos
|←─────────────────────────────────────→|
     ✓    ✓    ✓    ✓    ✓    ✓    ✗
   10:00 10:12 10:25 10:38 10:47 10:55 11:02
```

- **Registra** o timestamp de cada chamada
- **Remove** timestamps fora da janela (>60s atrás)
- **Bloqueia** se já houver 10 chamadas na janela
- **Aguarda** até que a chamada mais antiga saia da janela

### Fluxo de Uso

**Antes de cada chamada à API**:

```python
# 1. Aguarda se necessário
rate_limiter.wait_if_needed()

# 2. Faz a chamada
response = gemini_api.generate_content(prompt)

# 3. Registra a chamada
rate_limiter.record_call()
```

### Exemplo de Throttling

```
┌─────────────────────────────────────────────┐
│ Timestamp: 10:00:00                         │
│ Chamadas na janela: 0/10                    │
│ Ação: Procede imediatamente                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Timestamp: 10:00:55                         │
│ Chamadas na janela: 9/10                    │
│ Ação: Procede imediatamente                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Timestamp: 10:00:58                         │
│ Chamadas na janela: 10/10                   │
│ Ação: AGUARDA 3 segundos (até 10:01:01)     │
└─────────────────────────────────────────────┘
```

### Cálculo do Tempo de Espera

```python
# Chamada mais antiga: 10:00:00
# Agora: 10:00:58
# Tempo decorrido: 58 segundos
# Tempo de espera: 60 - 58 + 1 = 3 segundos (+1 margem de segurança)
```

### Onde É Usado

O rate limiter é aplicado em **3 pontos críticos**:

1. **Geração de Keywords** (1 chamada Gemini)
   - `keyword_generation_service.py:88-96`

2. **Extração de Tópicos** (1 chamada Gemini)
   - `news_service.py:612-617`

3. **Verificação de Similaridade** (1 chamada Gemini)
   - `news_service.py:699-709`

**Total**: ~3 chamadas Gemini por execução (bem abaixo do limite de 10/min)

---

## Coleta de Notícias

**Objetivo**: Coletar metadados e conteúdo completo de notícias relevantes.

### APIs Utilizadas

#### 1. GNews API - Top Headlines

**Endpoint**: `https://gnews.io/api/v4/top-headlines`

**Parâmetros**:
- `category`: general (categoria padrão)
- `lang`: en (idioma padrão)
- `country`: us (país padrão)
- `max`: 10 (artigos por chamada)

**Exemplo de Resposta**:
```json
{
  "articles": [
    {
      "title": "Breaking: New AI breakthrough announced",
      "description": "Scientists have achieved...",
      "url": "https://example.com/article1",
      "image": "https://example.com/image1.jpg",
      "publishedAt": "2025-10-10T14:30:00Z",
      "source": {
        "name": "TechNews",
        "url": "https://technews.com"
      }
    }
  ]
}
```

#### 2. GNews API - Search

**Endpoint**: `https://gnews.io/api/v4/search`

**Parâmetros**:
- `q`: "blockchain OR criptomoedas OR web3" (query booleana)
- `lang`: pt (do tópico)
- `country`: br (do tópico)
- `max`: 10

**Por Que Usar Ambos?**

- **Top Headlines**: Notícias gerais e de última hora (baseline)
- **Search**: Notícias específicas dos tópicos priorizados (personalização)

### Web Scraping com Newspaper3k

A GNews API retorna apenas **metadados** (título, descrição, URL).

Para obter o **conteúdo completo**, fazemos web scraping:

```python
from newspaper import Article

article = Article(url, config=config)
article.download()  # Baixa HTML
article.parse()     # Extrai conteúdo
content = article.article_html  # HTML limpo do artigo
```

**Configurações**:
- **User-Agent**: Chrome 128 (evita bloqueios)
- **Timeout**: 15 segundos
- **Formato**: HTML (preserva formatação)

### Detecção de Duplicatas

Antes de salvar, verificamos se a notícia já existe:

```python
if news_repo.find_by_url(article_url):
    logging.info("Artigo já existe, pulando")
    continue
```

**Critério**: URL única (campo UNIQUE no banco)

### Gerenciamento de Fontes

As fontes (news sources) são criadas automaticamente:

1. **Busca por URL** da fonte
2. **Se não existe**, busca por nome (pode ter URL diferente)
3. **Se não existe**, cria nova fonte
4. **Se ocorrer race condition**, busca novamente

Isso evita duplicação de fontes com URLs diferentes.

### Fluxo de Processamento

```
Para cada artigo da API:
  │
  ├─ Verificar se URL já existe no banco
  │  └─ Se sim: PULAR
  │
  ├─ Buscar ou criar fonte (news_source)
  │
  ├─ Fazer scraping do conteúdo completo
  │  └─ Se falhar: PULAR
  │
  ├─ Criar objeto News e validar
  │
  ├─ Salvar no banco de dados
  │
  └─ Adicionar à lista de categorização
```

### Tratamento de Erros

O sistema é resiliente a falhas:

- **Scraping falha**: Pula o artigo, continua com próximos
- **Fonte inválida**: Pula o artigo
- **Validação falha**: Pula o artigo
- **Race condition**: Tenta buscar novamente

**Logs detalhados** registram cada etapa e erro.

---

## Sistema de Blacklist Automático

**Objetivo**: Bloquear automaticamente domínios que falham consistentemente no scraping, registrando informações detalhadas para análise posterior por humanos.

### O Problema

Durante o scraping, alguns sites bloqueiam ou falham consistentemente:

- **403 Forbidden**: Site bloqueia explicitamente scraping
- **401 Unauthorized**: Requer autenticação/paywall
- **SSL Certificate Errors**: Problemas de certificado
- **Timeouts Recorrentes**: Site muito lento ou instável
- **429 Too Many Requests**: Rate limiting do site

Tentar fazer scraping desses sites **desperdiça tempo e recursos** em cada execução do job.

### A Solução

Sistema de **blacklist automático** que:

1. **Detecta erros críticos** durante o scraping
2. **Adiciona domínios problemáticos** à blacklist automaticamente
3. **Registra informações detalhadas** para análise humana posterior
4. **Pula scraping** de domínios bloqueados nas próximas execuções
5. **Permite remoção manual** após análise/correção

### Estrutura da Blacklist

Armazenada em JSON (`backend/app/data/scraping_blacklist.json`):

```json
{
  "seekingalpha.com": {
    "blocked_at": "2025-10-10T20:39:07.557Z",
    "error_type": "403 Forbidden",
    "error_count": 2,
    "last_url": "https://seekingalpha.com/news/...",
    "last_error_message": "Article download failed with 403 Client Error: Forbidden...",
    "reason": "Site blocks scraping with 403 Forbidden",
    "updated_at": "2025-10-10T21:15:23.891Z"
  },
  "reuters.com": {
    "blocked_at": "2025-10-10T20:42:15.234Z",
    "error_type": "401 Unauthorized",
    "error_count": 1,
    "last_url": "https://reuters.com/article/...",
    "last_error_message": "Article download failed with 401 Client Error: Unauthorized...",
    "reason": "Site requires authentication (401 Unauthorized)"
  }
}
```

### Tipos de Erros Detectados

| Erro | Quando Adiciona | Motivo |
|------|-----------------|--------|
| **403 Forbidden** | Imediatamente | Site bloqueia scraping explicitamente |
| **401 Unauthorized** | Imediatamente | Requer login/paywall |
| **SSL Certificate Error** | Imediatamente | Certificado inválido ou expirado |
| **Timeout (30s)** | Imediatamente | Site muito lento ou não responde |
| **429 Too Many Requests** | Imediatamente | Rate limiting do site |
| **503 Service Unavailable** | NÃO adiciona | Erro temporário, pode ser transitório |

### Fluxo de Funcionamento

```
┌──────────────────────────────────────┐
│ Scraping de URL iniciado             │
└──────────────────────────────────────┘
           ▼
┌──────────────────────────────────────┐
│ Verificar se domínio está bloqueado  │
│ scraping_blacklist.is_blocked(url)   │
└──────────────────────────────────────┘
           │
           ├─ Se BLOQUEADO: ─────────────┐
           │                             ▼
           │                  ┌──────────────────────┐
           │                  │ Pula scraping        │
           │                  │ Log warning          │
           │                  │ Retorna None         │
           │                  └──────────────────────┘
           │
           └─ Se NÃO bloqueado:
                      ▼
           ┌──────────────────────────┐
           │ Tenta fazer scraping     │
           │ (newspaper3k)            │
           └──────────────────────────┘
                      │
                      ├─ SUCESSO ──────────┐
                      │                    ▼
                      │         ┌─────────────────────┐
                      │         │ Retorna conteúdo    │
                      │         └─────────────────────┘
                      │
                      └─ ERRO ──────────┐
                                        ▼
                         ┌──────────────────────────────┐
                         │ Detectar tipo de erro:       │
                         │ • 403 Forbidden              │
                         │ • 401 Unauthorized           │
                         │ • SSL Error                  │
                         │ • Timeout                    │
                         │ • 429 Too Many Requests      │
                         └──────────────────────────────┘
                                        ▼
                         ┌──────────────────────────────┐
                         │ Se erro crítico:             │
                         │ add_to_blacklist(url, ...)   │
                         │ • Salva detalhes             │
                         │ • Incrementa contador        │
                         │ • Atualiza timestamp         │
                         └──────────────────────────────┘
                                        ▼
                         ┌──────────────────────────────┐
                         │ Log error                    │
                         │ Retorna None                 │
                         └──────────────────────────────┘
```

### Funcionalidades da Classe ScrapingBlacklist

#### 1. Verificar se Está Bloqueado

```python
if scraping_blacklist.is_blocked(url):
    logging.warning(f"Site bloqueado: {url}")
    return None
```

#### 2. Adicionar à Blacklist

```python
scraping_blacklist.add_to_blacklist(
    url="https://seekingalpha.com/news/...",
    error_type="403 Forbidden",
    error_message="Article download failed with 403 Client Error",
    reason="Site blocks scraping with 403 Forbidden"
)
```

**Comportamento**:
- Se domínio **já existe**: incrementa `error_count`, atualiza `last_error_message` e `updated_at`
- Se domínio **novo**: cria entrada com `error_count = 1` e `blocked_at = agora`
- **Salva automaticamente** no arquivo JSON após cada adição

#### 3. Obter Informações de Bloqueio

```python
info = scraping_blacklist.get_blocked_info(url)
# Retorna: {
#   "blocked_at": "2025-10-10T20:39:07.557Z",
#   "error_type": "403 Forbidden",
#   "error_count": 2,
#   "last_url": "https://...",
#   "last_error_message": "...",
#   "reason": "..."
# }
```

#### 4. Remover da Blacklist (Manual)

```python
# Após análise humana e correção
scraping_blacklist.remove_from_blacklist("https://example.com")
```

#### 5. Estatísticas

```python
stats = scraping_blacklist.get_statistics()
# Retorna: {
#   "total_blocked": 5,
#   "by_error_type": {
#     "403 Forbidden": 2,
#     "401 Unauthorized": 1,
#     "Timeout": 2
#   },
#   "domains": ["seekingalpha.com", "reuters.com", ...]
# }
```

### Exemplo de Log

**Primeira tentativa (erro detectado)**:

```
2025-10-10 14:23:45 - ERROR - Erro no scraping de https://seekingalpha.com/news/123: Article download failed with 403 Client Error: Forbidden
2025-10-10 14:23:45 - WARNING - ⚠️  DOMÍNIO BLOQUEADO AUTOMATICAMENTE: 'seekingalpha.com' (erro: 403 Forbidden)
```

**Próxima execução (domínio já bloqueado)**:

```
2025-10-10 20:15:30 - WARNING - Site na blacklist automática (bloqueado em 2025-10-10T14:23:45): https://seekingalpha.com/news/456 - Motivo: 403 Forbidden, 1 erro(s) registrado(s)
```

### Análise Humana Posterior

Para revisar domínios bloqueados:

1. **Ler arquivo JSON**:
   ```bash
   cat backend/app/data/scraping_blacklist.json
   ```

2. **Analisar informações**:
   - Verificar `error_type` e `error_count`
   - Ler `last_error_message` completa
   - Tentar acessar `last_url` manualmente
   - Decidir se é permanente ou temporário

3. **Tomar ação**:
   - **Se permanente**: manter na blacklist
   - **Se resolvido**: remover via API ou código
   - **Se precisa ajuste**: implementar solução (ex: headers especiais)

### Vantagens do Sistema

✅ **Automático**: Zero intervenção manual durante o job
✅ **Informativo**: Registra detalhes para análise posterior
✅ **Eficiente**: Evita desperdício de recursos em sites problemáticos
✅ **Persistente**: Blacklist sobrevive a reinicializações
✅ **Incremental**: Conta erros recorrentes do mesmo domínio
✅ **Reversível**: Permite remoção manual após análise

### Integração no Código

Arquivo: `backend/app/services/news_service.py:600-659`

```python
def scrape_article_content(self, url: str) -> str | None:
    # 1. Verificar blacklist
    if self.scraping_blacklist.is_blocked(url):
        info = self.scraping_blacklist.get_blocked_info(url)
        logging.warning(f"Site na blacklist: {url} ({info.get('error_type')})")
        return None

    # 2. Tentar scraping
    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        return article.article_html
    except Exception as e:
        error_str = str(e)

        # 3. Detectar tipo de erro
        error_type = None
        if '403' in error_str or 'Forbidden' in error_str:
            error_type = "403 Forbidden"
        elif '401' in error_str or 'Unauthorized' in error_str:
            error_type = "401 Unauthorized"
        elif 'SSL' in error_str or 'certificate' in error_str:
            error_type = "SSL Certificate Error"
        elif 'timeout' in error_str.lower():
            error_type = "Timeout"
        elif '429' in error_str:
            error_type = "429 Too Many Requests"

        # 4. Adicionar à blacklist se erro crítico
        if error_type:
            self.scraping_blacklist.add_to_blacklist(
                url=url,
                error_type=error_type,
                error_message=error_str[:500],
                reason=f"Site blocks scraping: {error_type}"
            )

        logging.error(f"Erro no scraping: {e}")
        return None
```

---

## Categorização Automática

**Objetivo**: Associar automaticamente cada notícia aos tópicos corretos usando IA.

### Fluxo em Batch

A categorização processa **todas as notícias de uma vez**, não uma por uma!

```
┌──────────────────────────────────────────┐
│ ETAPA 1: Extração de Tópicos            │
│ (1 CHAMADA GEMINI)                       │
├──────────────────────────────────────────┤
│ Input: 10 notícias                       │
│ Output: Lista de tópicos para cada uma   │
└──────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│ ETAPA 2: Verificação de Similaridade    │
│ (1 CHAMADA GEMINI, se necessário)       │
├──────────────────────────────────────────┤
│ Input: Tópicos extraídos                 │
│ Output: Mapeamento para tópicos existentes│
└──────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│ ETAPA 3: Criação de Novos Tópicos       │
├──────────────────────────────────────────┤
│ Cria tópicos que não existem no banco    │
└──────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────┐
│ ETAPA 4: Associação news ↔ topics       │
├──────────────────────────────────────────┤
│ Insere registros na tabela news_topics   │
└──────────────────────────────────────────┘
```

### Etapa 1: Extração de Tópicos

**Prompt para a IA**:

```
Analise o conteúdo de cada notícia no array JSON abaixo e, para CADA UMA,
extraia os principais temas macro.

Regras:
- Para cada notícia, retorne NO MÍNIMO 3 tópicos macro
- O tópico precisa estar na mesma linguagem da notícia! (REGRA MÁXIMA)
- Cada tópico deve ter no MÁXIMO 3 palavras (preferível 1 palavra)
- Tópicos em letras minúsculas, sem pontuação
- Foque em temas MACRO (conceitos gerais), não MICRO (detalhes)

Exemplo:
Notícia: "O Banco Central decidiu aumentar a taxa Selic em 0.5 ponto..."
Temas MICRO (evitar): "aumento da selic", "decisão do copom"
Temas MACRO (desejados): "política", "inflação", "economia"

Formato de Saída (JSON):
{
  "101": ["economia", "inflação", "política monetária"],
  "102": ["tecnologia", "inteligência artificial", "inovação"],
  "103": ["meio ambiente", "sustentabilidade", "energia renovável"]
}

Notícias para Análise:
[
  {"id": 101, "content": "O Comitê de Política Monetária..."},
  {"id": 102, "content": "Nova IA revoluciona setor..."},
  {"id": 103, "content": "Empresa investe em energia solar..."}
]
```

**Resposta da IA**:

```json
{
  "101": ["economia", "inflação", "política monetária"],
  "102": ["tecnologia", "inteligência artificial", "inovação"],
  "103": ["meio ambiente", "sustentabilidade", "energia renovável"]
}
```

### Etapa 2: Detecção de Similaridade

**Problema**: A IA pode extrair tópicos similares aos que já existem, mas com nomes diferentes.

Exemplos:
- "futebol nacional" é similar a "futebol" (já existe)
- "eleições presidenciais" é similar a "eleições" (já existe)

**Solução**: Verificar similaridade em batch!

**Prompt**:

```
Analise cada tópico da "lista_para_verificar" e encontre o tópico mais
similar semanticamente na "lista_existente".

Regras:
1. Similaridade Semântica: significado conceitual quase idêntico
2. Restrição de Idioma (CRÍTICA): só mapear se MESMO idioma
   - "soccer" NÃO pode mapear para "futebol" (idiomas diferentes)
3. Correspondência de Escopo (CRÍTICA): só mapear se escopo similar
   - NÃO: "futebol" → "esportes" (específico para geral)
   - SIM: "eleições presidenciais" → "eleições" (escopo similar)
4. Se não houver correspondência válida: retornar null

lista_para_verificar:
["futebol nacional", "eleições presidenciais", "soccer"]

lista_existente:
["futebol", "política", "esportes", "eleições"]

Formato de Saída (JSON):
{
  "futebol nacional": "futebol",
  "eleições presidenciais": "eleições",
  "soccer": null
}
```

### Etapa 3: Criação de Tópicos

Para cada tópico extraído que:
- **Não tem match exato** no banco
- **Não tem similaridade** detectada

Um **novo tópico é criado**:

```python
new_topic = Topic(name="inteligência artificial")
created_topic = topic_repo.create(new_topic)
```

### Etapa 4: Associação

Finalmente, associamos cada notícia aos seus tópicos:

```python
for topic_name in extracted_topics[news_id]:
    topic_model = topic_mapping[topic_name]
    news_topic_repo.create_association(news_id, topic_model.id)
```

**Tabela**: `news_topics` (M:N entre `news` e `topics`)

### Exemplo Completo

**Entrada**:
- Notícia 101: "Banco Central aumenta Selic para conter inflação"
- Notícia 102: "Nova IA da Google revoluciona tradução"

**Saída da Extração**:
```json
{
  "101": ["economia", "inflação", "política monetária"],
  "102": ["tecnologia", "inteligência artificial", "google"]
}
```

**Similaridade**:
- "política monetária" → "política" (similar, existente)
- Outros: sem similaridade

**Tópicos Criados**:
- "economia" (novo)
- "inflação" (novo)
- "tecnologia" (novo)
- "inteligência artificial" (novo)
- "google" (novo)

**Associações**:
- Notícia 101 ↔ economia, inflação, política
- Notícia 102 ↔ tecnologia, inteligência artificial, google

---

## Detecção de Similaridade

**Objetivo**: Evitar criar tópicos duplicados com nomes diferentes mas significados similares.

### O Problema

Usuários e a IA podem criar/extrair tópicos similares:

- "futebol" vs "futebol nacional"
- "política" vs "política brasileira"
- "IA" vs "inteligência artificial"
- "tech" vs "tecnologia"

Isso causa:
- **Fragmentação** de dados
- **Dificuldade** em buscar notícias
- **Redundância** no banco

### A Solução

Usar IA para detectar **similaridade semântica** e **mapear automaticamente**.

### Regras de Similaridade

A IA segue **3 regras críticas**:

#### 1. Similaridade Semântica

Conceito central deve ser quase idêntico.

- ✅ "futebol nacional" → "futebol"
- ✅ "eleições 2024" → "eleições"
- ❌ "gato" → "animal" (muito genérico)

#### 2. Restrição de Idioma

**NUNCA mapear tópicos em idiomas diferentes**, mesmo que sejam traduções.

- ❌ "soccer" → "futebol"
- ❌ "technology" → "tecnologia"
- ❌ "health" → "saúde"

**Motivo**: Notícias em inglês devem ficar separadas de notícias em português!

#### 3. Correspondência de Escopo

Evitar mapear tópicos de hierarquias diferentes.

- ❌ "futebol" → "esportes" (específico → geral)
- ❌ "eleição" → "votação" (geral → específico)
- ✅ "futebol brasileiro" → "futebol" (escopo similar)

### Funcionamento em Batch

**Input**:
- `topics_to_check`: ["futebol nacional", "eleições 2024", "soccer", "tech"]
- `existing_topics`: ["futebol", "política", "eleições", "tecnologia", "esportes"]

**Output**:
```json
{
  "futebol nacional": "futebol",
  "eleições 2024": "eleições",
  "soccer": null,
  "tech": null
}
```

**Ações**:
- "futebol nacional" → usar "futebol" (ID=1)
- "eleições 2024" → usar "eleições" (ID=5)
- "soccer" → criar novo tópico (idioma diferente)
- "tech" → criar novo tópico (escopo diferente de "tecnologia")

### Quando É Executado

A detecção de similaridade é usada em **2 momentos**:

1. **Durante categorização** de notícias
   - Evita criar tópicos duplicados automaticamente

2. **Quando usuário seleciona tópicos** (futuro)
   - Pode sugerir tópicos existentes similares

---

## Configurações

Todas as configurações estão centralizadas em:

**Arquivo**: `backend/app/config/news_collection_config.py`

### Parâmetros Principais

```python
NEWS_COLLECTION_CONFIG = {
    # CHAMADAS À API GNEWS
    "gnews_calls_per_job": 5,              # Total de chamadas por execução
    "gnews_top_headlines_calls": 1,        # Chamadas obrigatórias ao top-headlines
    "gnews_search_calls": 4,               # Chamadas de busca por tópico

    # DISTRIBUIÇÃO DE TÓPICOS
    "topics_to_select": 4,                 # Quantidade de tópicos a priorizar
    "searches_per_topic": 1,               # Buscas por tópico
    "keywords_per_search": 5,              # Keywords por busca

    # SISTEMA DE CACHE
    "cache_ttl_hours": 6,                  # Tempo de vida do cache
    "max_searches_per_topic_in_6h": 3,     # Máximo de buscas por tópico
    "cache_file_path": "backend/app/data/topic_search_cache.json",

    # ALGORITMO DE PRIORIZAÇÃO (SCORING)
    "score_user_weight": 10,               # Peso por usuário interessado
    "score_news_weight": 0.5,              # Peso (negativo) por notícia existente
    "score_diversity_bonus": 50,           # Bônus para tópicos nunca buscados
    "score_cache_penalty": 30,             # Penalidade por busca recente

    # IDIOMAS E PAÍSES
    "supported_languages": ["pt", "en"],
    "language_country_map": {
        "pt": "br",
        "en": "us"
    },
    "default_language": "en",
    "default_country": "us",

    # TÓPICOS DEFAULT (FALLBACK)
    "default_topics": [
        "tecnologia", "política", "economia", "saúde",
        "educação", "esportes", "entretenimento",
        "ciência", "meio ambiente", "segurança"
    ],

    # GNEWS API
    "gnews_max_articles_per_call": 10,
    "gnews_top_headlines_category": "general",

    # THROTTLING - GEMINI API
    "gemini_max_calls_per_minute": 10,
    "gemini_rate_limit_window_seconds": 60,
}
```

### Validação Automática

O arquivo valida as configurações ao ser importado:

```python
# Validação 1: Distribuição de chamadas
expected_search_calls = gnews_calls_per_job - gnews_top_headlines_calls
assert gnews_search_calls == expected_search_calls

# Validação 2: Distribuição de tópicos
expected_searches = topics_to_select × searches_per_topic
assert gnews_search_calls == expected_searches
```

Se houver inconsistência, o sistema **não inicia**.

### Como Ajustar

**Cenário 1**: Quero coletar mais notícias por execução

```python
"gnews_calls_per_job": 10,           # Era 5
"gnews_search_calls": 9,             # Era 4 (10 - 1)
"topics_to_select": 9,               # Era 4
```

**Cenário 2**: Quero diversificar mais os tópicos

```python
"score_diversity_bonus": 100,        # Era 50 (bônus maior)
"max_searches_per_topic_in_6h": 2,   # Era 3 (bloqueia antes)
```

**Cenário 3**: Quero mais keywords por busca

```python
"keywords_per_search": 10,           # Era 5
```

---

## Métricas e Monitoramento

### Logs do Job

Cada execução gera logs detalhados:

```
2025-10-10 14:00:00 - INFO - ================================================================================
2025-10-10 14:00:00 - INFO - JOB DE COLETA INTELIGENTE INICIADO
2025-10-10 14:00:00 - INFO - ================================================================================
2025-10-10 14:00:01 - INFO - [1/8] Carregando cache...
2025-10-10 14:00:01 - INFO - Cache carregado. 2 entradas antigas removidas.
2025-10-10 14:00:02 - INFO - [2/8] Selecionando 4 tópicos prioritários...
2025-10-10 14:00:02 - INFO - Métricas carregadas para 15 tópicos
2025-10-10 14:00:02 - INFO - Tópicos selecionados: ['tecnologia', 'política', 'economia', 'saúde']
2025-10-10 14:00:03 - INFO - [3/8] Gerando keywords para todos os tópicos em batch...
2025-10-10 14:00:05 - INFO - Keywords geradas com sucesso para 4 tópicos
2025-10-10 14:00:06 - INFO - [4/8] Coletando notícias do GNews...
2025-10-10 14:00:07 - INFO - GNews Top-Headlines: category=general, lang=en, country=us
2025-10-10 14:00:08 - INFO - GNews retornou 10 artigos
2025-10-10 14:00:09 - INFO - Search 1/4: tópico='tecnologia', query="blockchain OR criptomoedas...", artigos=8
...
2025-10-10 14:10:00 - INFO - [8/8] Coleta inteligente finalizada!
2025-10-10 14:10:00 - INFO - ================================================================================
2025-10-10 14:10:00 - INFO - RESUMO:
2025-10-10 14:10:00 - INFO -   - Tópicos priorizados: 4
2025-10-10 14:10:00 - INFO -   - Chamadas GNews: 5 (1 top-headlines + 4 search)
2025-10-10 14:10:00 - INFO -   - Artigos coletados: 42
2025-10-10 14:10:00 - INFO -   - Novos artigos salvos: 28
2025-10-10 14:10:00 - INFO -   - Novas fontes: 5
2025-10-10 14:10:00 - INFO - ================================================================================
```

### Visualizar Logs

**Via Docker**:
```bash
docker logs synapse-cron
docker logs synapse-cron --tail 100
docker logs synapse-cron --follow
```

**Arquivo de Log**:
```bash
cat /var/log/cron.log  # Dentro do container
```

### Métricas Importantes

| Métrica | Significado | Valor Esperado |
|---------|-------------|----------------|
| **Tópicos priorizados** | Quantidade de tópicos selecionados | 4 |
| **Chamadas GNews** | Total de requisições ao GNews | 5 (1% do limite) |
| **Chamadas Gemini** | Total de requisições à IA | ~3 (1.5% do limite) |
| **Artigos coletados** | Total retornado pelas APIs | 30-50 |
| **Novos artigos salvos** | Artigos únicos inseridos | 20-40 (excluindo duplicatas) |
| **Novas fontes** | Fontes criadas | 0-10 |
| **Tópicos criados** | Novos tópicos na categorização | 5-15 |
| **Tempo de execução** | Duração total do job | 5-10 minutos |

### Indicadores de Problemas

**Poucos artigos salvos (< 10)**:
- Cache pode estar saturado (muitas buscas recentes)
- Tópicos priorizados estão sem conteúdo novo
- Duplicatas excessivas

**Solução**: Limpar cache manualmente ou ajustar `max_searches_per_topic_in_6h`

**Erro de rate limiting**:
- Muitas chamadas Gemini em pouco tempo
- Ajustar `gemini_max_calls_per_minute`

**Scraping falhando muito**:
- Sites bloqueando User-Agent
- Timeout muito baixo
- Problemas de rede

### Consultas SQL Úteis

**Notícias coletadas nas últimas 24h**:
```sql
SELECT COUNT(*) FROM news
WHERE created_at > NOW() - INTERVAL '24 hours';
```

**Tópicos mais populares**:
```sql
SELECT t.name, COUNT(ut.user_id) as users
FROM topics t
LEFT JOIN user_topics ut ON t.id = ut.topic_id
GROUP BY t.name
ORDER BY users DESC;
```

**Fontes mais produtivas**:
```sql
SELECT ns.name, COUNT(n.id) as articles
FROM news_sources ns
LEFT JOIN news n ON ns.id = n.source_id
GROUP BY ns.name
ORDER BY articles DESC
LIMIT 10;
```

**Tópicos por notícia (média)**:
```sql
SELECT AVG(topic_count) as avg_topics_per_news
FROM (
  SELECT news_id, COUNT(topic_id) as topic_count
  FROM news_topics
  GROUP BY news_id
) subquery;
```

---

## Resumo Executivo

### O Que o Sistema Faz

1. **Prioriza** automaticamente os tópicos mais relevantes baseado em usuários e cobertura
2. **Gera** keywords inteligentes usando IA, evitando repetição
3. **Coleta** notícias de múltiplas fontes via GNews API
4. **Extrai** conteúdo completo por web scraping
5. **Categoriza** automaticamente usando IA semântica
6. **Evita** duplicação de tópicos e notícias
7. **Respeita** rigorosamente limites de APIs

### Principais Algoritmos

| Algoritmo | Complexidade | Objetivo |
|-----------|--------------|----------|
| **Priorização de Tópicos** | O(n) | Calcular score baseado em demanda/oferta |
| **Cache de Buscas** | O(n) | Evitar buscas repetitivas |
| **Geração de Keywords (Batch)** | O(1) chamadas IA | Criar keywords contextuais |
| **Categorização (Batch)** | O(1) chamadas IA | Extrair tópicos de notícias |
| **Similaridade (Batch)** | O(1) chamadas IA | Mapear tópicos similares |

### Consumo de Recursos

**Por execução (a cada 6 horas)**:
- ~5 chamadas GNews (1% do limite diário)
- ~3 chamadas Gemini (1.5% do limite diário)
- 30-50 requisições HTTP (scraping)
- 5-10 minutos de processamento
- 20-40 notícias novas salvas

**Por dia (4 execuções)**:
- 20 chamadas GNews (20% do limite)
- 12 chamadas Gemini (6% do limite)
- 80-160 notícias novas

### Pontos Fortes

✅ **Totalmente automatizado** - zero intervenção manual
✅ **Inteligente** - prioriza tópicos relevantes dinamicamente
✅ **Eficiente** - otimiza uso de APIs caras
✅ **Resiliente** - tolera falhas e continua processando
✅ **Escalável** - ajustável via configuração
✅ **Observável** - logs detalhados de cada etapa

### Limitações

⚠️ **Dependência de APIs externas** (GNews, Gemini)
⚠️ **Scraping pode falhar** em sites com proteção anti-bot
⚠️ **IA pode alucinar** tópicos ou keywords irrelevantes
⚠️ **Custo** se limites de APIs forem ultrapassados

---

## Referências de Código

### Arquivos Principais

- `backend/app/jobs/collect_news.py` - Ponto de entrada do job
- `backend/app/services/news_service.py` - Orquestrador principal
- `backend/app/services/topic_prioritization_service.py` - Algoritmo de priorização
- `backend/app/services/keyword_generation_service.py` - Geração de keywords
- `backend/app/services/topic_similarity_service.py` - Detecção de similaridade
- `backend/app/utils/topic_search_cache.py` - Sistema de cache
- `backend/app/utils/api_rate_limiter.py` - Rate limiting
- `backend/app/utils/scraping_blacklist.py` - Blacklist automático de scraping
- `backend/app/repositories/topic_stats_repository.py` - Consultas de métricas
- `backend/app/config/news_collection_config.py` - Configurações

### Fluxo Completo

```python
# 1. Executar job
run_collection_job()
  └─> news_service.collect_news_intelligently()

# 2. Priorizar tópicos
prioritization_service.get_prioritized_topics(count=4)
  └─> topic_stats_repo.get_topic_metrics(days=7)
  └─> cache.count_searches_in_period(hours=6)
  └─> _calculate_scores()

# 3. Gerar keywords
keyword_service.generate_keywords_batch(topic_names)
  └─> cache.get_used_keywords(hours=6)
  └─> rate_limiter.wait_if_needed()
  └─> ai_service.generate_content(prompt)
  └─> rate_limiter.record_call()

# 4. Coletar notícias
call_top_headlines()
search_articles_via_gnews(query)

# 5. Processar notícias
scrape_article_content(url)
news_repo.create(article)

# 6. Categorizar
_categorize_articles_batch(articles)
  └─> _extract_topics_from_content_batch()  # 1 chamada Gemini
  └─> similarity_service.find_similar_topics_batch()  # 1 chamada Gemini
  └─> topic_repo.create(new_topic)
  └─> news_topic_repo.create_association()

# 7. Salvar cache
cache.save()
```

---

**Documento criado em**: 2025-10-10
**Versão**: 1.0
**Sistema**: Synapse News Aggregator
**Autor**: Documentação Automática via Claude Code
