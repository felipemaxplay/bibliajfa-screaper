"""Exporta o JSON para TXT otimizado para RAG (AnythingLLM, NotebookLM, Gemini).

Modos:
  capitulo  um arquivo por capítulo  (data/rag/NAA/capitulos/01-genesis/01.txt)
  livro     um arquivo por livro     (data/rag/NAA/livros/01-genesis.txt)
  secao     um arquivo por seção     (data/rag/NAA/secoes/01-pentateuco.txt)

Cada versículo recebe a referência completa (ex.: "Gênesis 1:1 No princípio..."),
para que qualquer trecho recuperado isoladamente seja citável.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from .books import BOOKS, SECTIONS, section_slug
from .config import TranslationConfig
from .scraper import load_records

log = logging.getLogger(__name__)

MODOS = ("capitulo", "livro", "secao")
_POR_NUM = {b.num: b for b in BOOKS}


def _linhas_capitulo(cfg: TranslationConfig, nome: str, cap: int, versos: list[dict]) -> list[str]:
    ordenados = sorted(versos, key=lambda v: v["versiculo"])
    return [f"{nome} {cap}:{v['versiculo']} {v['texto']}" for v in ordenados]


def _agrupar(registros: list[dict]) -> dict[int, dict[int, list[dict]]]:
    livros: dict[int, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in registros:
        livros[r["livro_num"]][r["capitulo"]].append(r)
    return livros


def _texto_livro(cfg: TranslationConfig, livro_num: int, capitulos: dict[int, list[dict]]) -> str:
    book = _POR_NUM[livro_num]
    blocos = [f"{book.nome} ({cfg.codigo})"]
    for cap in sorted(capitulos):
        linhas = _linhas_capitulo(cfg, book.nome, cap, capitulos[cap])
        blocos.append(f"{book.nome} {cap}\n" + "\n".join(linhas))
    return "\n\n".join(blocos) + "\n"


def export_rag(cfg: TranslationConfig, modo: str, saida: Path | None = None) -> Path:
    if modo not in MODOS:
        raise SystemExit(f"Modo inválido: {modo}. Use um de: {', '.join(MODOS)}")
    registros = load_records(cfg.json_path)
    if not registros:
        raise SystemExit(f"JSON vazio ou inexistente: {cfg.json_path}. Rode o scraper primeiro.")

    pasta_modo = {"capitulo": "capitulos", "livro": "livros", "secao": "secoes"}[modo]
    raiz = (saida or cfg.json_path.parents[1] / "rag" / cfg.codigo.upper()) / pasta_modo
    livros = _agrupar(registros)
    total = 0

    if modo == "capitulo":
        for livro_num, caps in sorted(livros.items()):
            book = _POR_NUM[livro_num]
            largura = max(2, len(str(book.capitulos)))
            pasta = raiz / book.pasta
            pasta.mkdir(parents=True, exist_ok=True)
            for cap, versos in sorted(caps.items()):
                corpo = [f"{book.nome} {cap} ({cfg.codigo})", ""]
                corpo += _linhas_capitulo(cfg, book.nome, cap, versos)
                (pasta / f"{cap:0{largura}d}.txt").write_text("\n".join(corpo) + "\n", encoding="utf-8")
                total += 1

    elif modo == "livro":
        raiz.mkdir(parents=True, exist_ok=True)
        for livro_num, caps in sorted(livros.items()):
            book = _POR_NUM[livro_num]
            (raiz / f"{book.pasta}.txt").write_text(_texto_livro(cfg, livro_num, caps), encoding="utf-8")
            total += 1

    else:  # secao
        raiz.mkdir(parents=True, exist_ok=True)
        for i, (nome, ini, fim) in enumerate(SECTIONS, 1):
            partes = [f"{nome} ({cfg.codigo})"]
            for livro_num in range(ini, fim + 1):
                if livro_num in livros:
                    partes.append(_texto_livro(cfg, livro_num, livros[livro_num]).rstrip("\n"))
            if len(partes) == 1:
                continue
            (raiz / f"{section_slug(i, nome)}.txt").write_text("\n\n\n".join(partes) + "\n", encoding="utf-8")
            total += 1

    log.info("%d arquivo(s) gerados em %s", total, raiz)
    return raiz
