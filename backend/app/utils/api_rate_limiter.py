"""
Sistema de throttling/rate limiting para controlar chamadas à API do Gemini.
Garante que não ultrapassaremos o limite de 10 chamadas por minuto.
"""

import time
import logging
from typing import List


class APIRateLimiter:
    """
    Controla a taxa de chamadas a uma API para respeitar limites de rate limiting.

    Exemplo de uso:
        limiter = APIRateLimiter(max_calls=10, window_seconds=60)

        # Antes de cada chamada à API:
        limiter.wait_if_needed()
        result = api.call()
        limiter.record_call()
    """

    def __init__(self, max_calls: int, window_seconds: int):
        """
        Inicializa o rate limiter.

        Args:
            max_calls: Número máximo de chamadas permitidas na janela de tempo
            window_seconds: Tamanho da janela de tempo em segundos
        """
        self.max_calls = max_calls
        self.window = window_seconds
        self.call_timestamps: List[float] = []

        logging.info(
            f"APIRateLimiter inicializado: máximo de {max_calls} chamadas "
            f"a cada {window_seconds} segundos"
        )

    def wait_if_needed(self) -> None:
        """
        Aguarda o tempo necessário se o limite de chamadas foi atingido.

        Esta função deve ser chamada ANTES de fazer uma chamada à API.
        Se o limite de chamadas já foi atingido na janela de tempo atual,
        esta função aguardará até que seja seguro fazer uma nova chamada.
        """
        now = time.time()

        # Limpar timestamps fora da janela de tempo
        self._clean_old_timestamps(now)

        # Se atingiu o limite, calcular tempo de espera
        if len(self.call_timestamps) >= self.max_calls:
            oldest_call = self.call_timestamps[0]
            time_since_oldest = now - oldest_call
            wait_time = self.window - time_since_oldest + 1  # +1 para margem de segurança

            if wait_time > 0:
                logging.warning(
                    f"Rate limit atingido ({self.max_calls} chamadas em {self.window}s). "
                    f"Aguardando {wait_time:.1f} segundos..."
                )
                time.sleep(wait_time)

                # Após esperar, limpar timestamps antigos novamente
                now = time.time()
                self._clean_old_timestamps(now)

                logging.info("Aguardo concluído. Prosseguindo com chamada à API.")

    def record_call(self) -> None:
        """
        Registra uma chamada que acabou de ser realizada.

        Esta função deve ser chamada IMEDIATAMENTE APÓS fazer uma chamada à API.
        """
        timestamp = time.time()
        self.call_timestamps.append(timestamp)

        logging.debug(
            f"Chamada registrada. Total de chamadas na janela atual: "
            f"{len(self.call_timestamps)}/{self.max_calls}"
        )

    def _clean_old_timestamps(self, current_time: float) -> None:
        """
        Remove timestamps que estão fora da janela de tempo.

        Args:
            current_time: Timestamp atual (time.time())
        """
        self.call_timestamps = [
            ts for ts in self.call_timestamps
            if current_time - ts < self.window
        ]

    def get_current_call_count(self) -> int:
        """
        Retorna o número de chamadas feitas na janela de tempo atual.

        Returns:
            Número de chamadas na janela atual
        """
        now = time.time()
        self._clean_old_timestamps(now)
        return len(self.call_timestamps)

    def get_time_until_next_available_slot(self) -> float:
        """
        Retorna quanto tempo (em segundos) até que uma nova chamada possa ser feita.

        Returns:
            Segundos até próxima chamada disponível (0 se já pode chamar)
        """
        now = time.time()
        self._clean_old_timestamps(now)

        if len(self.call_timestamps) < self.max_calls:
            return 0.0

        oldest_call = self.call_timestamps[0]
        time_since_oldest = now - oldest_call
        wait_time = self.window - time_since_oldest

        return max(0.0, wait_time)

    def reset(self) -> None:
        """
        Reseta o contador de chamadas.

        Use com cuidado! Normalmente não é necessário chamar este método,
        pois o rate limiter se auto-gerencia.
        """
        self.call_timestamps = []
        logging.info("Rate limiter resetado.")
