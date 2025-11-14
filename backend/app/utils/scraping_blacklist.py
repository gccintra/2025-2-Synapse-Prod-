"""
Sistema de blacklist automático para scraping de notícias.
Adiciona sites problemáticos automaticamente e registra informações para análise.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse


class ScrapingBlacklist:
    """
    Gerencia uma blacklist de sites que falham consistentemente no scraping.

    A blacklist é persistida em arquivo JSON e contém informações detalhadas
    sobre cada site bloqueado para análise posterior por humanos.
    """

    def __init__(self, blacklist_file_path: str):
        """
        Inicializa a blacklist.

        Args:
            blacklist_file_path: Caminho do arquivo JSON de blacklist
        """
        self.blacklist_file_path = blacklist_file_path
        self.blacklist_data: Dict[str, Dict] = {}

    def load(self) -> Dict[str, Dict]:
        """
        Carrega a blacklist do disco.

        Returns:
            Dicionário com dados da blacklist
        """
        if not os.path.exists(self.blacklist_file_path):
            logging.info(f"Arquivo de blacklist não existe. Criando novo: {self.blacklist_file_path}")
            self.blacklist_data = {}
            return self.blacklist_data

        try:
            with open(self.blacklist_file_path, 'r', encoding='utf-8') as f:
                self.blacklist_data = json.load(f)
            logging.info(f"Blacklist carregada com sucesso. {len(self.blacklist_data)} domínios bloqueados.")
            return self.blacklist_data
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON da blacklist: {e}. Criando nova blacklist vazia.")
            self.blacklist_data = {}
            return self.blacklist_data
        except Exception as e:
            logging.error(f"Erro ao carregar blacklist: {e}. Criando nova blacklist vazia.")
            self.blacklist_data = {}
            return self.blacklist_data

    def save(self) -> None:

        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.blacklist_file_path), exist_ok=True)

            with open(self.blacklist_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.blacklist_data, f, indent=2, ensure_ascii=False)

            logging.debug(f"Blacklist salva com sucesso: {self.blacklist_file_path}")
        except Exception as e:
            logging.error(f"Erro ao salvar blacklist: {e}", exc_info=True)

    def get_domain(self, url: str) -> Optional[str]:
        """
        Extrai o domínio de uma URL.

        Args:
            url: URL completa

        Returns:
            Domínio (ex: 'example.com') ou None se inválida
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            # Remover 'www.' se presente
            if domain.startswith('www.'):
                domain = domain[4:]

            return domain if domain else None
        except Exception as e:
            logging.warning(f"Erro ao extrair domínio de '{url}': {e}")
            return None

    def is_blocked(self, url: str) -> bool:
        """
        Verifica se uma URL está na blacklist.

        Args:
            url: URL a verificar

        Returns:
            True se bloqueado, False caso contrário
        """
        domain = self.get_domain(url)
        if not domain:
            return False

        return domain in self.blacklist_data

    def add_to_blacklist(
        self,
        url: str,
        error_type: str,
        error_message: str,
        reason: str = "Site blocks scraping or fails consistently"
    ) -> bool:
        """
        Adiciona um domínio à blacklist automaticamente.

        Args:
            url: URL que causou o erro
            error_type: Tipo do erro (ex: '403 Forbidden', 'SSL Error', 'Timeout')
            error_message: Mensagem de erro completa
            reason: Motivo descritivo do bloqueio

        Returns:
            True se adicionado/atualizado, False se falhou
        """
        domain = self.get_domain(url)
        if not domain:
            logging.warning(f"Não foi possível extrair domínio de '{url}'. Não adicionado à blacklist.")
            return False

        # Se já existe, incrementar contador
        if domain in self.blacklist_data:
            self.blacklist_data[domain]["error_count"] += 1
            self.blacklist_data[domain]["last_url"] = url
            self.blacklist_data[domain]["last_error_message"] = error_message
            self.blacklist_data[domain]["last_error_type"] = error_type
            self.blacklist_data[domain]["updated_at"] = datetime.now().isoformat()

            logging.info(
                f"Domínio '{domain}' já na blacklist. Contador atualizado: "
                f"{self.blacklist_data[domain]['error_count']} erros."
            )
        else:
            # Adicionar novo domínio
            self.blacklist_data[domain] = {
                "blocked_at": datetime.now().isoformat(),
                "error_type": error_type,
                "error_count": 1,
                "last_url": url,
                "last_error_message": error_message[:500],  # Limitar tamanho
                "reason": reason
            }

            logging.warning(
                f"⚠️  DOMÍNIO BLOQUEADO AUTOMATICAMENTE: '{domain}' (erro: {error_type})"
            )

        # Salvar imediatamente
        self.save()
        return True

    def get_blocked_info(self, url: str) -> Optional[Dict]:
        """
        Retorna informações sobre um domínio bloqueado.

        Args:
            url: URL a verificar

        Returns:
            Dicionário com informações ou None se não bloqueado
        """
        domain = self.get_domain(url)
        if not domain:
            return None

        return self.blacklist_data.get(domain)

    def remove_from_blacklist(self, url: str) -> bool:
        """
        Remove um domínio da blacklist (para revisão manual).

        Args:
            url: URL do domínio a remover

        Returns:
            True se removido, False se não estava na blacklist
        """
        domain = self.get_domain(url)
        if not domain:
            return False

        if domain in self.blacklist_data:
            del self.blacklist_data[domain]
            self.save()
            logging.info(f"Domínio '{domain}' removido da blacklist.")
            return True

        return False

    def get_all_blocked_domains(self) -> list[str]:
        """
        Retorna lista de todos os domínios bloqueados.

        Returns:
            Lista de domínios
        """
        return list(self.blacklist_data.keys())

    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas sobre a blacklist.

        Returns:
            Dicionário com estatísticas
        """
        if not self.blacklist_data:
            return {
                "total_blocked": 0,
                "by_error_type": {}
            }

        error_types = {}
        for domain_data in self.blacklist_data.values():
            error_type = domain_data.get("error_type", "Unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return {
            "total_blocked": len(self.blacklist_data),
            "by_error_type": error_types,
            "domains": self.get_all_blocked_domains()
        }
