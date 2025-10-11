# Manual de Coleta Manual de Notícias

## Introdução

O script `manual_news_collection.py` permite executar a coleta de notícias manualmente através da linha de comando, com total controle sobre os parâmetros de configuração. É ideal para:

- 🧪 **Testes e debugging** do sistema de coleta
- 🔬 **Experimentação** com diferentes configurações
- 🎯 **Coletas pontuais** com parâmetros específicos
- 📊 **Análise de desempenho** com configurações variadas

## Requisitos

- Python 3.12+
- Docker containers rodando (banco de dados)
- Variáveis de ambiente configuradas:
  - `GNEWS_API_KEY` - Chave da API GNews
  - `DATABASE_URL` - URL do banco PostgreSQL
  - `GEMINI_API_KEY` - Chave da API Google Gemini (para categorização)

## Instalação

O script está localizado em `backend/app/scripts/manual_news_collection.py` e pode ser executado diretamente:

```bash
# Dentro do container Docker
docker exec synapse-backend python -m app.scripts.manual_news_collection

# Ou com ambiente virtual ativado
cd backend
python -m app.scripts.manual_news_collection
```

## Uso Básico

### Coleta Inteligente (Padrão)

```bash
python -m app.scripts.manual_news_collection
```

Este comando executa a coleta inteligente usando as configurações padrão definidas em `news_collection_config.py`.

### Ver Ajuda

```bash
python -m app.scripts.manual_news_collection --help
```

## Modos de Operação

### Modo Intelligent (Recomendado)

Utiliza o algoritmo de coleta inteligente que:
- Prioriza tópicos baseado em métricas de usuários
- Gera keywords automaticamente via IA
- Gerencia cache de buscas
- Categoriza notícias em batch

```bash
python -m app.scripts.manual_news_collection --mode intelligent
```

### Modo Legacy

Utiliza o método legado de coleta, mais simples e direto:

```bash
python -m app.scripts.manual_news_collection --mode legacy --topics technology sports
```

## Parâmetros Disponíveis

### Parâmetros Gerais

| Parâmetro | Tipo | Descrição | Padrão |
|-----------|------|-----------|---------|
| `--mode` | `intelligent\|legacy` | Modo de coleta | `intelligent` |
| `--verbose` | flag | Ativa logs detalhados | `false` |
| `--dry-run` | flag | Simula sem salvar no banco | `false` |

### Parâmetros de Configuração

| Parâmetro | Tipo | Descrição | Padrão (config) |
|-----------|------|-----------|-----------------|
| `--topics-count` | int | Número de tópicos a selecionar | `9` |
| `--search-calls` | int | Número de chamadas de search | `9` |
| `--max-articles` | int | Artigos máximos por chamada | `10` |
| `--keywords-per-search` | int | Keywords por busca | `4` |

### Parâmetros de Idioma/País

| Parâmetro | Tipo | Descrição | Padrão (config) |
|-----------|------|-----------|-----------------|
| `--language` | str | Código do idioma (pt, en) | `en` |
| `--country` | str | Código do país (br, us) | `us` |
| `--category` | str | Categoria top-headlines | `general` |

### Parâmetros do Modo Legacy

| Parâmetro | Tipo | Descrição | Exemplo |
|-----------|------|-----------|---------|
| `--topics` | list | Tópicos específicos | `technology sports` |

### Flags Especiais

| Flag | Descrição |
|------|-----------|
| `--skip-cache` | Ignora cache de buscas (força busca nova) |
| `--dry-run` | Modo simulação (não salva no banco) |
| `--verbose` | Logs detalhados (DEBUG level) |

## Exemplos Práticos

### 1. Coleta Inteligente Padrão

```bash
python -m app.scripts.manual_news_collection
```

Executa com todas as configurações padrão.

### 2. Coleta Reduzida para Testes

```bash
python -m app.scripts.manual_news_collection \
  --topics-count 3 \
  --search-calls 5 \
  --max-articles 5 \
  --verbose
```

Coleta menor e mais rápida para testes.

### 3. Coleta em Português/Brasil

```bash
python -m app.scripts.manual_news_collection \
  --language pt \
  --country br \
  --category general \
  --verbose
```

Foca em notícias brasileiras em português.

### 4. Coleta em Inglês/EUA

```bash
python -m app.scripts.manual_news_collection \
  --language en \
  --country us \
  --category technology
```

Foca em notícias de tecnologia dos EUA.

### 5. Coleta Intensiva

```bash
python -m app.scripts.manual_news_collection \
  --topics-count 15 \
  --search-calls 20 \
  --max-articles 10 \
  --keywords-per-search 6
```

Coleta mais abrangente (consome mais créditos da API).

### 6. Modo Legacy com Tópicos Específicos

```bash
python -m app.scripts.manual_news_collection \
  --mode legacy \
  --topics technology sports entertainment
```

Usa método legado com tópicos específicos.

### 7. Ignorar Cache (Forçar Nova Busca)

```bash
python -m app.scripts.manual_news_collection \
  --skip-cache \
  --verbose
```

Ignora cache e força novas buscas para todos os tópicos.

### 8. Modo Dry-Run (Simulação)

```bash
python -m app.scripts.manual_news_collection \
  --dry-run \
  --verbose
```

Simula a coleta sem salvar nada no banco (útil para testes).

### 9. Coleta Completa com Todos os Parâmetros

```bash
python -m app.scripts.manual_news_collection \
  --mode intelligent \
  --topics-count 10 \
  --search-calls 15 \
  --max-articles 10 \
  --keywords-per-search 5 \
  --language pt \
  --country br \
  --category general \
  --skip-cache \
  --verbose
```

Exemplo completo com todos os parâmetros customizados.

## Modo Dry-Run

O modo dry-run é ideal para testar configurações sem afetar o banco de dados:

```bash
python -m app.scripts.manual_news_collection --dry-run --verbose
```

**Funcionalidades do dry-run:**
- ✅ Executa toda a lógica de coleta
- ✅ Chama APIs externas (GNews, Gemini)
- ✅ Processa e valida dados
- ❌ **NÃO** salva artigos no banco
- ❌ **NÃO** salva fontes no banco
- ❌ **NÃO** cria associações

**Nota:** O modo dry-run ainda está em desenvolvimento e pode não funcionar completamente.

## Saída do Script

O script exibe três seções de informação:

### 1. Configurações

```
================================================================================
CONFIGURAÇÕES DA COLETA
================================================================================
Modo: INTELLIGENT
Tópicos a selecionar: 9
Chamadas de search: 9
Keywords por busca: 4
Artigos por chamada: 10
Idioma: pt
País: br
Categoria top-headlines: general
================================================================================
```

### 2. Logs de Execução

```
2025-10-11 14:30:00 - INFO - [1/8] Carregando cache...
2025-10-11 14:30:01 - INFO - [2/8] Selecionando 9 tópicos prioritários...
2025-10-11 14:30:02 - INFO - Tópicos selecionados: ['tecnologia', 'política', ...]
...
```

### 3. Resumo Final

```
================================================================================
RESUMO DA COLETA
================================================================================
Novos artigos: 45
Novas fontes: 3
Tempo decorrido: 125.34s
================================================================================
```

## Troubleshooting

### Erro: GNEWS_API_KEY não configurada

```
ValueError: A variável de ambiente GNEWS_API_KEY não foi configurada.
```

**Solução:** Configure a variável de ambiente no arquivo `.env`:

```bash
GNEWS_API_KEY=sua_chave_aqui
```

### Erro: Limite de API atingido (429)

```
Error 429: Too Many Requests
```

**Solução:**
- Aguarde alguns minutos antes de tentar novamente
- Reduza `--search-calls` para fazer menos chamadas
- Verifique seu plano da API GNews

### Erro: Banco de dados não acessível

```
SQLALCHEMY ERROR: could not connect to server
```

**Solução:**
- Verifique se os containers Docker estão rodando: `docker compose ps`
- Inicie os containers: `docker compose up -d`
- Verifique a variável `DATABASE_URL` no `.env`

### Script muito lento

**Soluções:**
- Reduza `--topics-count` e `--search-calls`
- Reduza `--max-articles`
- Use `--verbose` para identificar gargalos
- Verifique logs para sites com scraping lento (blacklist automática)

### Nenhum artigo coletado

**Causas possíveis:**
1. **Artigos já existem no banco**: Tente `--skip-cache`
2. **Parâmetros muito restritivos**: Ajuste idioma/país/categoria
3. **Falha no scraping**: Verifique logs com `--verbose`

## Notas Técnicas

### Overrides de Configuração

O script **não modifica** o arquivo `news_collection_config.py`. Todos os parâmetros são aplicados temporariamente apenas para a execução atual.

### Cache de Tópicos

O cache de buscas é mantido entre execuções. Use `--skip-cache` para ignorá-lo temporariamente.

### Throttling da API

O script respeita automaticamente os limites de rate limiting:
- **GNews**: 2s de delay entre chamadas
- **Gemini**: 10 chamadas/minuto máximo

### Categorização por IA

A categorização de notícias usa o Google Gemini e é feita em batch para otimização:
- 1 chamada para extração de tópicos
- 1 chamada para verificação de similaridade (se necessário)

### Blacklist Automática

Sites que falham consistentemente no scraping são automaticamente adicionados à blacklist para não desperdiçar tempo em chamadas futuras.

## Próximos Passos

Após executar a coleta manual, você pode:

1. **Verificar no banco de dados:**
   ```sql
   SELECT COUNT(*) FROM news;
   SELECT * FROM news ORDER BY created_at DESC LIMIT 10;
   ```

2. **Testar API:**
   ```bash
   curl http://localhost:5001/api/news
   ```

3. **Ver no frontend:**
   ```
   http://localhost:5173
   ```

## Referências

- [Documentação GNews API](https://gnews.io/docs/v4)
- [Configurações do Sistema](../app/config/news_collection_config.py)
- [NewsCollectService](../app/services/news_collect_service.py)
- [Cron Job de Coleta](../app/jobs/collect_news.py)

---

**Última atualização:** 2025-10-11
**Versão:** 1.0.0
