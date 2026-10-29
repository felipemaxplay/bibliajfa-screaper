"""Orquestra a extração capítulo a capítulo e grava o JSON (com retomada)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .books import BOOKS, Book
from .config import TranslationConfig
from .http_client import FetchError, PoliteClient
from .parser import parse_html, parse_json

log = logging.getLogger(__name__)


def load_records(path: Path) -> list[dict]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_records(path: Path, registros: list[dict]) -> None:
    """Escrita atômica para não corromper o JSON se o processo for interrompido."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def fetch_chapter(client: PoliteClient, cfg: TranslationConfig, book: Book, chapter: int) -> list[tuple[int, str]]:
    api = cfg.api_url(book, chapter)
    if api:
        resp = client.get(api)
        return parse_json(resp.json())
    resp = client.get(cfg.page_url(book, chapter))
    ctype = resp.headers.get("Content-Type", "")
    if "json" in ctype:
        return parse_json(resp.json())
    return parse_html(resp.text, cfg)


def _validar(versos: list[tuple[int, str]]) -> str | None:
    if not versos:
        return "nenhum versículo encontrado"
    nums = [n for n, _ in versos]
    if nums[0] != 1 or nums != list(range(1, len(nums) + 1)):
        return f"numeração inesperada: {nums[:5]}...{nums[-3:]}"
    return None


def scrape(cfg: TranslationConfig, books: list[Book] | None = None, resume: bool = True) -> Path:
    books = books or BOOKS
    registros = load_records(cfg.json_path) if resume else []
    feitos = {(r["livro_num"], r["capitulo"]) for r in registros}
    client = PoliteClient(cfg)
    falhas: list[str] = []

    for book in books:
        for cap in range(1, book.capitulos + 1):
            if (book.num, cap) in feitos:
                continue
            try:
                versos = fetch_chapter(client, cfg, book, cap)
            except FetchError as exc:
                log.error("%s %d: %s", book.nome, cap, exc)
                falhas.append(f"{book.nome} {cap}")
                continue
            problema = _validar(versos)
            if problema:
                log.warning("%s %d: %s (url: %s)", book.nome, cap, problema, cfg.page_url(book, cap))
                if not versos:
                    falhas.append(f"{book.nome} {cap}")
                    continue
            for num, texto in versos:
                registros.append({
                    "traducao": cfg.codigo,
                    "livro_num": book.num,
                    "livro_nome": book.nome,
                    "capitulo": cap,
                    "versiculo": num,
                    "texto": texto,
                })
            log.info("%s %d: %d versículos", book.nome, cap, len(versos))
        # checkpoint ao fim de cada livro
        registros.sort(key=lambda r: (r["livro_num"], r["capitulo"], r["versiculo"]))
        save_records(cfg.json_path, registros)

    if falhas:
        log.warning("Capítulos com falha (rode novamente para retomar): %s", ", ".join(falhas))
    log.info("JSON salvo em %s (%d versículos)", cfg.json_path, len(registros))
    return cfg.json_path
