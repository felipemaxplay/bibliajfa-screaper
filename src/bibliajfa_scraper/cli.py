"""Interface de linha de comando: python -m bibliajfa_scraper <comando>."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .books import parse_book_range
from .config import TRANSLATIONS, get_translation
from .exporter import export_txt
from .scraper import scrape


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bibliajfa_scraper", description=__doc__)
    p.add_argument("-v", "--verbose", action="store_true", help="logs detalhados")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scrape", help="extrai uma tradução para data/json/")
    s.add_argument("-t", "--translation", default="NAA")
    s.add_argument("-b", "--books", help="livros, ex.: 1, 1-5, 1,3,40-42 (padrão: todos)")
    s.add_argument("--min-delay", type=float)
    s.add_argument("--max-delay", type=float)
    s.add_argument("--no-resume", action="store_true", help="ignora o JSON existente")

    e = sub.add_parser("export", help="gera a árvore TXT a partir do JSON")
    e.add_argument("-t", "--translation", default="NAA")
    e.add_argument("-o", "--output", type=Path, help="pasta de saída (padrão: data/txt/<TRADUCAO>)")

    sub.add_parser("list", help="lista as traduções configuradas")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.cmd == "list":
        for cod, cfg in sorted(TRANSLATIONS.items()):
            print(f"{cod}\t{cfg.url_template.format(slug=cfg.slug, book_code='01O', chapter=1)}")
        return

    cfg = get_translation(args.translation)
    if args.cmd == "scrape":
        if args.min_delay is not None:
            cfg.min_delay = args.min_delay
        if args.max_delay is not None:
            cfg.max_delay = max(args.max_delay, cfg.min_delay)
        scrape(cfg, parse_book_range(args.books), resume=not args.no_resume)
    elif args.cmd == "export":
        export_txt(cfg, args.output)
