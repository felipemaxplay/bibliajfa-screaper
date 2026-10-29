"""Cliente HTTP com delays aleatórios, retry e backoff exponencial."""

from __future__ import annotations

import logging
import random
import time

import requests

from .config import TranslationConfig

log = logging.getLogger(__name__)

RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    pass


class PoliteClient:
    def __init__(self, cfg: TranslationConfig) -> None:
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update(cfg.headers)
        self._last_request = 0.0

    def _polite_sleep(self) -> None:
        alvo = random.uniform(self.cfg.min_delay, self.cfg.max_delay)
        decorrido = time.monotonic() - self._last_request
        if decorrido < alvo:
            time.sleep(alvo - decorrido)

    def get(self, url: str) -> requests.Response:
        ultimo_erro: Exception | None = None
        for tentativa in range(1, self.cfg.max_retries + 1):
            self._polite_sleep()
            try:
                resp = self.session.get(url, timeout=self.cfg.timeout)
                self._last_request = time.monotonic()
                if resp.status_code in RETRY_STATUS:
                    espera = self._backoff(tentativa, resp.headers.get("Retry-After"))
                    log.warning("HTTP %s em %s (tentativa %d); aguardando %.1fs",
                                resp.status_code, url, tentativa, espera)
                    ultimo_erro = FetchError(f"HTTP {resp.status_code}")
                    time.sleep(espera)
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                self._last_request = time.monotonic()
                ultimo_erro = exc
                espera = self._backoff(tentativa)
                log.warning("Falha em %s (tentativa %d): %s; aguardando %.1fs",
                            url, tentativa, exc, espera)
                time.sleep(espera)
        raise FetchError(f"Falha ao buscar {url} após {self.cfg.max_retries} tentativas: {ultimo_erro}")

    def _backoff(self, tentativa: int, retry_after: str | None = None) -> float:
        if retry_after and retry_after.isdigit():
            return float(retry_after)
        return self.cfg.backoff_base ** tentativa + random.uniform(0, 1)
