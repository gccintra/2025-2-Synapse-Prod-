# Manual de Execução da Coleta de Notícias

## Introdução

O sistema de coleta de notícias usa uma abordagem **simplificada e confiável** que pode ser executada manualmente a qualquer momento. É ideal para:

- 🧪 **Testes e debugging** do sistema de coleta
- 🔄 **Execução sob demanda** quando necessário
- 📊 **Monitoramento de funcionamento** do sistema
- 🛠️ **Troubleshooting** de problemas

## Requisitos

- Python 3.12+
- Docker containers rodando (banco de dados)
- Variáveis de ambiente configuradas:
  - `GNEWS_API_KEY` - Chave da API GNews
  - `DATABASE_URL` - URL do banco PostgreSQL
  - `GEMINI_API_KEY` - Chave da API Google Gemini (para keywords)

## Sistema Atual (Simplificado)

O sistema atual usa **apenas uma abordagem** de coleta:

### collect_news_simple()
1. **Busca todos os tópicos ativos** no banco de dados
2. **Gera keywords em batch** usando Gemini AI (1 chamada)
3. **Para cada tópico**: busca notícias no GNews + salva no banco
4. **Sem cache, sem priorização, sem configurações complexas**

---

## Execução Manual

### Comando Principal

```bash
# Dentro do container Docker (recomendado)
docker exec synapse-backend python /app/backend/app/jobs/collect_news.py

# Ou via module
docker exec synapse-backend python -m app.jobs.collect_news

# Execução local (se ambiente configurado)
cd backend
python -m app.jobs.collect_news
```

### Verificação Rápida

```bash
# Verificar se container está rodando
docker ps | grep synapse-backend

# Verificar logs em tempo real
docker logs -f synapse-backend

# Testar conectividade
docker exec synapse-backend python -c "
from app.repositories.topic_repository import TopicRepository
print('Topics ativos:', len(TopicRepository().get_all_active()))
"
```

---

## Saída do Sistema

### 1. Logs de Início

```
================================================================================
JOB DE COLETA SIMPLIFICADA INICIADO
================================================================================
AIService inicializado com sucesso (modelo=gemini-2.5-flash, timeout=60s).
KeywordGenerationService inicializado
```

### 2. Processamento por Etapas

```
================================================================================
INICIANDO COLETA SIMPLIFICADA DE NOTÍCIAS
================================================================================
[1/3] Buscando tópicos ativos do banco de dados...
Encontrados 8 tópicos ativos: ['technology', 'politics', 'business', ...]

[2/3] Coletando notícias para 8 tópicos...
    Gerando keywords para todos os tópicos em batch...
Keywords geradas para 8 tópicos

  [1/8] Buscando notícias para o tópico: 'technology' (ID=1)
    Query para 'technology': "Apple iPhone" OR "Google AI" OR "Microsoft Windows"
GNews retornou 10 artigos
    Search encontrou: 10 artigos

  [2/8] Buscando notícias para o tópico: 'politics' (ID=2)
    Query para 'politics': "Joe Biden" OR "Donald Trump" OR "US Congress"
...
```

### 3. Processamento de Artigos

```
[3/3] Processando e salvando notícias...
  Processando 10 artigos do tópico 'technology'...
    Notícia salva: 'Apple iPhone 17 Pro vs Apple iPhone 16...' → tópico 'technology' (ID=1)
    Notícia salva: 'Wikipedia blames ChatGPT for falling traffic...' → tópico 'technology' (ID=1)
⚠️  DOMÍNIO BLOQUEADO AUTOMATICAMENTE: 'bloomberg.com' (erro: 403 Forbidden)
...
```

### 4. Resumo Final

```
================================================================================
COLETA SIMPLIFICADA FINALIZADA!
RESUMO:
  - Tópicos processados: 8 (do banco de dados)
  - Estratégia: 1 busca por tópico com keywords de IA em batch
  - Chamadas GNews: 8
  - Artigos coletados: 80
  - Novos artigos salvos: 57
  - Novas fontes: 13
================================================================================
JOB FINALIZADO COM SUCESSO
Resumo: 57 notícias e 13 fontes salvas
```

---

## Consumo de APIs

### Por Execução (8 tópicos ativos):

| API | Chamadas | Uso do Limite | Observações |
|-----|----------|---------------|-------------|
| **GNews** | 8 | ~8% do limite diário | 1 call por tópico ativo |
| **Gemini** | 1 | ~0.5% do limite diário | Batch keyword generation |

### Rate Limiting Automático:
- **GNews**: 2 segundos entre chamadas
- **Gemini**: 60 segundos timeout
- **Retry**: Automático para erros 429

---

## Troubleshooting

### ❌ Erro: GNEWS_API_KEY não configurada

```
KeyError: 'GNEWS_API_KEY'
```

**Solução:** Configure no arquivo `.env`:
```bash
GNEWS_API_KEY=sua_chave_aqui
```

### ❌ Erro: Limite de API atingido (429)

```
HTTPError: 429 Client Error: Too Many Requests
```

**Soluções:**
- Aguarde alguns minutos antes de tentar novamente
- Verifique seu plano da API GNews (100 calls/day gratuito)
- Monitor de uso: https://gnews.io/dashboard

### ❌ Erro: Banco de dados não acessível

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solução:**
```bash
# Verificar containers
docker compose ps

# Reiniciar se necessário
docker compose down
docker compose up -d

# Verificar DATABASE_URL no .env
```

### ❌ Erro: Gemini API falhando

```
GoogleAPIError: 403 Forbidden
```

**Soluções:**
- Verifique `GEMINI_API_KEY` no `.env`
- Confirme que API está ativa no Google Cloud Console
- Verifique cotas/billing no projeto

### ⚠️ Poucos artigos coletados

**Causas possíveis:**
1. **Artigos duplicados**: URLs já existem no banco
2. **Sites bloqueados**: Muitos domínios na blacklist
3. **Keywords muito específicas**: IA gerou termos muito restritivos

**Debugging:**
```bash
# Ver blacklist atual
docker exec synapse-backend cat /tmp/scraping_blacklist.json | jq '.blocked_domains | length'

# Ver domínios bloqueados
docker exec synapse-backend cat /tmp/scraping_blacklist.json | jq '.blocked_domains | keys'

# Contar notícias no banco
docker exec synapse-backend python -c "
from app.repositories.news_repository import NewsRepository
print('Total de notícias:', NewsRepository().count_all())
"
```

### 📊 Sistema muito lento

**Otimizações:**
1. **Blacklist crescendo**: Sites problemáticos são bloqueados automaticamente
2. **Rate limiting**: 2s por chamada GNews é necessário
3. **Scraping timeout**: Sites lentos são abandonados após 30s

**Tempo esperado**: 2-4 minutos para 8 tópicos

---

## Verificação Pós-Execução

### 1. Verificar no Banco de Dados

```sql
-- Últimas notícias coletadas
SELECT title, created_at, source_id
FROM news
ORDER BY created_at DESC
LIMIT 10;

-- Contagem por tópico
SELECT t.name, COUNT(n.id) as news_count
FROM topics t
LEFT JOIN news n ON t.id = n.topic_id
GROUP BY t.name
ORDER BY news_count DESC;

-- Notícias das últimas 24h
SELECT COUNT(*) FROM news
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### 2. Testar APIs

```bash
# Testar endpoint de notícias
curl http://localhost:5001/api/news | jq '.news | length'

# Testar feed personalizado
curl -H "Authorization: Bearer SEU_TOKEN" \
     http://localhost:5001/api/news/for-you | jq '.news | length'

# Verificar tópicos
curl http://localhost:5001/api/topics | jq '.topics | length'
```

### 3. Verificar Frontend

```bash
# Abrir no navegador
open http://localhost:5173

# Ou testar conectividade
curl -I http://localhost:5173
```

---

## Configurações do Sistema

### Parâmetros Hardcoded

O sistema atual usa valores fixos (sem arquivo de config):

```python
# GNews Search Parameters
search_params = {
    'lang': 'en',        # Inglês fixo
    'country': 'us',     # Estados Unidos fixo
    'max': 10,           # 10 artigos por tópico
}

# Rate Limiting
GNEWS_DELAY = 2          # 2 segundos entre calls
SCRAPING_TIMEOUT = 30    # 30s timeout para scraping
GEMINI_TIMEOUT = 60      # 60s timeout para IA
```

### Modificar Comportamento

Para alterar parâmetros, edite diretamente:
- **NewsCollectService**: `backend/app/services/news_collect_service.py`
- **Palavras-chave**: Prompt no `KeywordGenerationService`
- **Rate limiting**: `backend/app/utils/api_rate_limiter.py`

---

## Dados Gerados

### Blacklist Automática

**Localização**: `/tmp/scraping_blacklist.json`

```bash
# Ver blacklist
docker exec synapse-backend cat /tmp/scraping_blacklist.json | jq

# Limpar blacklist (se necessário)
docker exec synapse-backend rm /tmp/scraping_blacklist.json
```

### Logs Persistentes

```bash
# Ver logs históricos
docker logs synapse-backend | grep "JOB DE COLETA" -A 20

# Logs em tempo real
docker logs -f synapse-backend
```

---

## Próximos Passos

### Automatização

Para execução automática, configure cron:

```bash
# Editar crontab
crontab -e

# Executar a cada 6 horas
0 */6 * * * docker exec synapse-backend python /app/backend/app/jobs/collect_news.py
```

### Monitoramento

Monitore execuções via:
1. **Logs Docker**: Sucesso/falhas da execução
2. **Banco de dados**: Volume de notícias coletadas
3. **Blacklist**: Crescimento de domínios bloqueados

### Melhorias Futuras

1. **Detecção de duplicatas por título** (planejado)
2. **Múltiplas fontes** além do GNews
3. **Configurações via variáveis de ambiente**
4. **Dashboard de monitoramento**

---

## Referências

- [Sistema de Coleta - Documentação Principal](../SISTEMA_COLETA_NOTICIAS.md)
- [GNews API Documentation](https://gnews.io/docs/v4)
- [NewsCollectService](../app/services/news_collect_service.py)
- [Job Principal](../app/jobs/collect_news.py)

---

**Última atualização**: 2025-10-21
**Versão**: Sistema Simplificado v2.0