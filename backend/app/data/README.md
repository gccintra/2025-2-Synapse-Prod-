# Diretório de Dados - Sistema Simplificado

Este diretório faz parte da estrutura do sistema de coleta de notícias, mas atualmente **não contém arquivos dinâmicos** devido à simplificação da arquitetura.

## Estado Atual do Sistema

O sistema de coleta foi **simplificado** e não utiliza mais cache complexo ou armazenamento local extensivo de dados temporários.

### Arquivos Não Mais Utilizados

❌ **`topic_search_cache.json`** - **REMOVIDO**
- **Motivo**: Sistema de priorização e cache complexo foi eliminado
- **Substituto**: Não há cache - cada execução processa todos os tópicos ativos
- **Benefício**: Menos complexidade, sempre processamento completo

### Arquivos Ativos (Localizados Externamente)

✅ **`/tmp/scraping_blacklist.json`** - **ATIVO**
- **Localização**: `/tmp/scraping_blacklist.json` (não neste diretório)
- **Descrição**: Lista de domínios bloqueados automaticamente por falharem no scraping
- **Gerenciamento**: Automático via `app/utils/scraping_blacklist.py`

## Arquivos de Dados Externos

### `/tmp/scraping_blacklist.json`

**Estrutura Atual**:
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
    },
    "seekingalpha.com": {
      "reason": "403 Forbidden",
      "blocked_at": "2025-10-21T02:33:38.775Z",
      "attempts": 2
    }
  }
}
```

**Tipos de Bloqueio Automático**:
- `403 Forbidden` - Site bloqueia scraping explicitamente
- `SSL Error` - Certificados inválidos ou problemas SSL
- `Timeout Error` - Sites que não respondem em 30s
- `Network Error` - Problemas de conectividade

**Visualização**:
```bash
# Ver blacklist atual
cat /tmp/scraping_blacklist.json | jq

# Ver estatísticas
cat /tmp/scraping_blacklist.json | jq '.blocked_domains | length'

# Ver domínios bloqueados recentemente
cat /tmp/scraping_blacklist.json | jq '.blocked_domains | to_entries[] | select(.value.blocked_at > "2025-10-21") | .key'
```

## Dados Simplificados

### O que mudou com a simplificação:

#### ❌ Removido:
- **Cache de buscas por tópico** (topic_search_cache.json)
- **Sistema de priorização** (não há mais pontuação de tópicos)
- **Histórico de execuções** (logs são suficientes)
- **Métricas complexas** (estatísticas via logs)

#### ✅ Mantido:
- **Blacklist automática** de domínios problemáticos
- **Logs estruturados** para monitoramento
- **Rate limiting** simples e eficaz

### Vantagens da Abordagem Atual:

1. **Menos Estado**: Sem arquivos de cache complexos para gerenciar
2. **Stateless**: Cada execução é independente
3. **Mais Confiável**: Menos arquivos para corromper ou dessincronizar
4. **Mais Simples**: Fácil de entender e debugar

## Monitoramento de Dados

### Via Logs (Recomendado)

O sistema atual monitora dados através de **logs estruturados**:

```bash
# Ver execução mais recente
docker logs synapse-backend | grep "JOB DE COLETA"

# Ver estatísticas da última execução
docker logs synapse-backend | grep "RESUMO" -A 10

# Ver domínios bloqueados em tempo real
docker logs synapse-backend | grep "BLOQUEADO AUTOMATICAMENTE"
```

### Via Banco de Dados

Dados persistentes estão no **banco de dados**:

```sql
-- Tópicos ativos
SELECT id, name, is_active FROM topics WHERE is_active = true;

-- Estatísticas de notícias por tópico
SELECT t.name, COUNT(n.id) as news_count
FROM topics t
LEFT JOIN news n ON t.id = n.topic_id
GROUP BY t.name;

-- Notícias coletadas nas últimas 24h
SELECT COUNT(*) FROM news WHERE created_at > NOW() - INTERVAL '24 hours';
```

## Limpeza e Manutenção

### Resetar Blacklist (se necessário)

```bash
# Limpar blacklist (o sistema recriará automaticamente)
sudo rm /tmp/scraping_blacklist.json

# Ou resetar conteúdo
echo '{"blocked_domains": {}}' | sudo tee /tmp/scraping_blacklist.json
```

### Verificação de Integridade

```bash
# Verificar se sistema está funcionando
docker exec synapse-backend python -c "
from app.services.news_collect_service import NewsCollectService
from app.utils.scraping_blacklist import ScrapingBlacklist

print('Sistema de coleta: OK')
print('Blacklist:', ScrapingBlacklist.get_blocked_count(), 'domínios bloqueados')
"
```

## Migração do Sistema Anterior

Se você está migrando do sistema anterior complexo:

### Arquivos Antigos para Remover:

```bash
# Cache antigo (não mais utilizado)
rm -f backend/app/data/topic_search_cache.json

# Configurações antigas (refatoradas)
rm -f backend/app/config/news_collection_config.py
```

### Verificar Limpeza:

```bash
# Verificar se diretório data está limpo
ls -la backend/app/data/

# Deve mostrar apenas:
# README.md (este arquivo)
# Possivelmente .gitkeep ou estar vazio
```

---

## Considerações Finais

O sistema atual prioriza **simplicidade e confiabilidade** sobre recursos complexos:

- ✅ **Menos arquivos de estado** = menos pontos de falha
- ✅ **Processamento sempre completo** = sem dependência de cache
- ✅ **Logs centralizados** = monitoramento mais fácil
- ✅ **Blacklist automática** = proteção contra sites problemáticos

Para análise avançada de dados, utilize:
1. **Logs do Docker** para execução e performance
2. **Banco de dados** para estatísticas de conteúdo
3. **Blacklist em /tmp/** para problemas de scraping

---

**Última atualização**: 2025-10-21
**Versão**: Sistema Simplificado v2.0