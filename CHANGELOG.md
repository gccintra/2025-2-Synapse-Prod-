# Changelog

Todo o histórico de mudanças deste projeto será documentado neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.2.0] - 2025-12-02

### ✨ Adicionado (Added)

- **Sistema de Newsletter Inteligente:** Implementado sistema completo de newsletter com resumos automatizados de notícias utilizando IA Gemini, agendamento via cron job, e personalização por usuário com templates responsivos.
- **Autenticação com Google OAuth:** Adicionado login social com Google OAuth2, sistema de múltiplos provedores de autenticação, sincronização automática de contas e resolução de conflitos de e-mail.
- **Serviço Avançado de Web Scraping:** Desenvolvido sistema inteligente de extração de conteúdo usando newspaper4k, com sanitização de HTML, suporte a mídia embarcada (vídeos, tweets, iframes), e blacklist automática para sites problemáticos.
- **Histórico de Leitura do Usuário:** Implementado rastreamento automático de artigos lidos com timestamps para análise de comportamento e personalização.
- **Sistema de Notícias Salvas:** Funcionalidade para usuários salvarem artigos favoritos para leitura posterior.
- **Tópicos Personalizados:** Permitir que usuários criem e gerenciem tópicos customizados além dos tópicos padrão do sistema.
- **Integração CI/CD com GHCR:** Pipeline automatizado para publicação de imagens Docker no GitHub Container Registry com suporte a cron jobs em containers.

### 🔧 Melhorado (Improved)

- **Modelo de Dados Expandido:** Adicionadas novas entidades (UserProvider, UserReadHistory, UserSavedNews, CustomTopic) para suporte às novas funcionalidades.
- **Cobertura de Testes:** Aumentada cobertura de testes para mais de 90% com testes unitários e de integração abrangentes.
- **Sistema de Logs:** Implementados logs estruturados para melhor diagnóstico e monitoramento do sistema.
- **Rate Limiting:** Controle inteligente de chamadas à API Gemini (máximo 10 chamadas por minuto) para otimização de custos.

### 🐛 Corrigido (Fixed)

- **Imagens de Notícias Principais:** Corrigido problema de corrupção de imagens principais dos artigos.
- **Duplicação de Histórico:** Solucionado problema de registros duplicados de leitura no mesmo dia.
- **Responsividade Mobile:** Correções em componentes que não funcionavam adequadamente em dispositivos móveis.
- **Inicialização Docker:** Resolvidos problemas de inicialização de containers com cron jobs configurados.

---

## [0.1.0-alpha] - 2025-09-30

### ✨ Adicionado (Added)

- **Autenticação de Usuário:** Implementado registro, login e logout de usuários com sessões seguras baseadas em cookies JWT.
- **Gerenciamento de Perfil:** Usuários podem visualizar, editar suas informações (nome, e-mail, data de nascimento) e alterar a senha.
- **Gerenciamento de Tópicos:** Funcionalidade para usuários adicionarem e removerem tópicos de interesse do seu perfil.
- **Gerenciamento de Fontes de Notícias:** Usuários podem selecionar e desmarcar fontes de notícias preferidas para personalizar seu feed.
- **Coleta Automatizada de Notícias:** Criado um job agendado (cron) que roda a cada 6 horas para buscar e salvar novas notícias utilizando a GNews API e web scraping.
- **Interface do Usuário (Frontend):** Desenvolvidas as telas de Login, Registro, Gerenciamento de Conta e Adição de Fontes com React e Tailwind CSS.
- **Documentação da API:** Adicionada documentação interativa da API utilizando Swagger/OpenAPI.
- **Estrutura de Testes:** Configurado ambiente de testes com Pytest para o back-end, incluindo testes para rotas e serviços.
