"""Exporta o JSON de uma tradução para uma árvore de arquivos TXT."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from .books import BOOKS
from .config import TranslationConfig
from .scraper import load_records

log = logging.getLogger(__name__)

_POR_NUM = {b.num: b for b in BOOKS}


def export_txt(cfg: TranslationConfig, saida: Path | None = None) -> Path:
    registros = load_records(cfg.json_path)
    if not registros:
        raise SystemExit(f"JSON vazio ou inexistente: {cfg.json_path}. Rode o scraper primeiro.")

    raiz = saida or cfg.txt_dir
    capitulos: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for r in registros:
        capitulos[(r["livro_num"], r["capitulo"])].append(r)

    for (livro_num, cap), versos in sorted(capitulos.items()):
        book = _POR_NUM[livro_num]
        largura = max(2, len(str(book.capitulos)))
        pasta = raiz / book.pasta
        pasta.mkdir(parents=True, exist_ok=True)
        linhas = [f"{v['versiculo']} {v['texto']}" for v in sorted(versos, key=lambda v: v["versiculo"])]
        (pasta / f"{cap:0{largura}d}.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    log.info("%d capítulos exportados para %s", len(capitulos), raiz)
    return raiz
