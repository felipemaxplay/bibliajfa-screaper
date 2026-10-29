#!/usr/bin/env python3
"""Inspeciona uma página do site para descobrir se há API JSON ou como o HTML é estruturado.

Uso:
    python scripts/inspect_site.py https://bibliajfa.com.br/app/naa/01O/1

Salva o HTML em debug/ (ignorado pelo Git) e imprime um relatório curto.
Cole o relatório no chat para ajustarmos o parser.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) bibliajfa-scraper/0.1 inspect"}
API_HINT = re.compile(r"""["'`]((?:https?:)?//[^"'`\s]+|/[A-Za-z0-9_\-./{}$]*(?:api|json|biblia|versiculo|chapter|capitulo)[A-Za-z0-9_\-./{}$?=&]*)["'`]""", re.I)


def main(url: str) -> None:
    sess = requests.Session()
    sess.headers.update(HEADERS)
    resp = sess.get(url, timeout=30)
    print(f"[status] {resp.status_code}  [content-type] {resp.headers.get('Content-Type')}")
    print(f"[url final] {resp.url}")

    out = Path("debug")
    out.mkdir(exist_ok=True)
    (out / "pagina.html").write_text(resp.text, encoding="utf-8")
    print(f"[html salvo] {out / 'pagina.html'} ({len(resp.text)} bytes)")

    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"[title] {soup.title.get_text(strip=True) if soup.title else None}")

    if soup.find("script", id="__NEXT_DATA__"):
        print("[aviso] __NEXT_DATA__ presente (Next.js): os dados podem estar embutidos no HTML")
    if re.search(r"window\.__\w+__\s*=", resp.text):
        print("[aviso] estado inicial embutido em window.__...__")

    candidatos = {
        "[data-verse]": soup.select("[data-verse], [data-versiculo], [data-v]"),
        "id v1/verse1": soup.find_all(id=re.compile(r"^(v|ver|vers|verse|versiculo)[-_]?\d+$", re.I)),
        "class verse/versiculo": soup.find_all(class_=re.compile(r"verse|versiculo|vers", re.I)),
    }
    print("\n[candidatos a versículo]")
    for nome, els in candidatos.items():
        print(f"  {nome}: {len(els)}")
        for el in els[:2]:
            print("    ", str(el)[:220].replace("\n", " "))

    scripts = [urljoin(resp.url, s["src"]) for s in soup.find_all("script", src=True)]
    host = urlparse(resp.url).netloc
    print(f"\n[scripts] {len(scripts)}")
    achados: set[str] = set()
    for texto in [s.get_text() for s in soup.find_all("script") if not s.get("src")]:
        achados.update(m.group(1) for m in API_HINT.finditer(texto))
    for src in scripts:
        print("  ", src)
        if urlparse(src).netloc != host:
            continue
        try:
            js = sess.get(src, timeout=30).text
        except requests.RequestException:
            continue
        achados.update(m.group(1) for m in API_HINT.finditer(js))

    print(f"\n[possíveis endpoints] {len(achados)}")
    for ep in sorted(achados)[:60]:
        print("  ", ep)

    print("\nDica: abra o DevTools (F12) > Network > Fetch/XHR, recarregue a página e")
    print("veja se alguma requisição JSON retorna os versículos. Copie a URL dela.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
