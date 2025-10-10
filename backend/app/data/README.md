# Diretório de Dados Dinâmicos

Este diretório contém arquivos JSON gerados e atualizados automaticamente pelo sistema de coleta de notícias.

## Arquivos

### `topic_search_cache.json`
**Descrição**: Cache de buscas por tópico nas últimas 6 horas.

**Estrutura**:
```json
{
  "tecnologia": {
    "searches": [
      {
        "keywords": ["IA", "machine learning"],
        "timestamp": "2025-10-10T14:00:00",
        "language": "pt",
        "country": "br",
        "news_found": 8
      }
    ]
  }
}
```

**Propósito**:
- Evitar buscar o mesmo tópico repetidamente
- Registrar keywords já utilizadas
- Aplicar penalidades de cache no algoritmo de priorização

**Gerenciamento**:
- Automaticamente limpo a cada 6 horas
- Lido e salvo em cada execução do job

---

### `scraping_blacklist.json`
**Descrição**: Lista de domínios bloqueados automaticamente por falharem no scraping.

**Estrutura**:
```json
{
  "seekingalpha.com": {
    "blocked_at": "2025-10-10T20:39:07.557Z",
    "error_type": "403 Forbidden",
    "error_count": 2,
    "last_url": "https://seekingalpha.com/news/...",
    "last_error_message": "Article download failed with 403...",
    "reason": "Site blocks scraping with 403 Forbidden",
    "updated_at": "2025-10-10T21:15:23.891Z"
  }
}
```

**Propósito**:
- Evitar tentar fazer scraping de sites que bloqueiam consistentemente
- Registrar informações detalhadas para análise humana posterior
- Economizar tempo e recursos

**Tipos de Erro que Adicionam à Blacklist**:
- `403 Forbidden` - Site bloqueia scraping explicitamente
- `401 Unauthorized` - Requer autenticação/paywall
- `SSL Certificate Error` - Certificado inválido ou expirado
- `Timeout (30s)` - Site muito lento ou não responde
- `429 Too Many Requests` - Rate limiting do site

**Gerenciamento**:
- Domínios adicionados automaticamente quando erros críticos ocorrem
- Remoção manual via código após análise
- Contador de erros incrementado para domínios recorrentes

---

## Observações Importantes

⚠️ **Não commitar no Git**: Estes arquivos contêm dados dinâmicos e devem estar no `.gitignore`.

📊 **Análise Manual**: Os arquivos podem ser visualizados a qualquer momento para análise:
```bash
# Ver cache de buscas
cat backend/app/data/topic_search_cache.json | jq

# Ver blacklist de scraping
cat backend/app/data/scraping_blacklist.json | jq

# Ver estatísticas da blacklist (via código)
# scraping_blacklist.get_statistics()
```

🔧 **Limpeza Manual**: Se necessário, limpar os arquivos manualmente:
```bash
# Resetar cache (o sistema recriará)
echo '{}' > backend/app/data/topic_search_cache.json

# Resetar blacklist (o sistema recriará)
echo '{}' > backend/app/data/scraping_blacklist.json
```

---

**Última atualização**: 2025-10-10
