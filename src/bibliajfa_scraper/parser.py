"""Extração de versículos a partir de JSON (API) ou HTML (DOM)."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from .config import TranslationConfig

NUM_KEYS = ("versiculo", "verso", "verse", "number", "numero", "num", "v", "n")
TEXT_KEYS = ("texto", "text", "content", "conteudo", "verse_text", "t")
_ATTR_NUM = ("data-verse", "data-versiculo", "data-v", "data-number", "data-num")
_ID_RE = re.compile(r"^(?:v|ver|vers|verse|versiculo)[-_]?(\d+)$", re.I)
_CLASS_RE = re.compile(r"(?:^|[-_ ])(?:verse|versiculo|vers)(?:$|[-_ ])", re.I)
_LEAD_NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[.\-–]?\s+(.+)$", re.S)


def _limpar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


# ---------------------------------------------------------------- JSON
def parse_json(payload: Any) -> list[tuple[int, str]]:
    """Procura recursivamente uma lista de objetos com número e texto de versículo."""
    if isinstance(payload, list) and payload and all(isinstance(i, dict) for i in payload):
        versos = _versos_de_lista(payload)
        if versos:
            return versos
    if isinstance(payload, dict):
        for valor in payload.values():
            achados = parse_json(valor)
            if achados:
                return achados
    if isinstance(payload, list):
        for item in payload:
            achados = parse_json(item)
            if achados:
                return achados
    return []


def _versos_de_lista(itens: list[dict]) -> list[tuple[int, str]]:
    saida: list[tuple[int, str]] = []
    for item in itens:
        chaves = {k.lower(): v for k, v in item.items()}
        num = next((chaves[k] for k in NUM_KEYS if k in chaves), None)
        texto = next((chaves[k] for k in TEXT_KEYS if k in chaves), None)
        if num is None or not isinstance(texto, str):
            return []
        try:
            saida.append((int(num), _limpar(texto)))
        except (TypeError, ValueError):
            return []
    return saida


# ---------------------------------------------------------------- HTML
def parse_html(html: str, cfg: TranslationConfig) -> list[tuple[int, str]]:
    soup = BeautifulSoup(html, "html.parser")
    for lixo in soup(["script", "style", "noscript"]):
        lixo.decompose()

    if cfg.verse_selector:
        versos = _por_seletor(soup, cfg)
        if versos:
            return versos

    return (
        _por_atributos(soup)
        or _por_classes(soup)
        or _por_texto_corrido(soup)
    )


def _num_e_texto(el: Tag, cfg: TranslationConfig | None = None) -> tuple[int, str] | None:
    if cfg and cfg.verse_number_selector:
        n_el = el.select_one(cfg.verse_number_selector)
        t_el = el.select_one(cfg.verse_text_selector) if cfg.verse_text_selector else None
        if n_el:
            m = re.search(r"\d+", n_el.get_text())
            if m:
                if t_el:
                    texto = t_el.get_text(" ")
                else:
                    n_el.extract()
                    texto = el.get_text(" ")
                return int(m.group()), _limpar(texto)
    for attr in _ATTR_NUM:
        if el.has_attr(attr) and str(el[attr]).isdigit():
            texto = _limpar(el.get_text(" "))
            m = _LEAD_NUM_RE.match(texto)
            if m and int(m.group(1)) == int(el[attr]):
                texto = m.group(2)
            return int(el[attr]), texto
    m_id = _ID_RE.match(el.get("id", "") or "")
    if m_id:
        texto = _limpar(el.get_text(" "))
        m = _LEAD_NUM_RE.match(texto)
        if m and int(m.group(1)) == int(m_id.group(1)):
            texto = m.group(2)
        return int(m_id.group(1)), texto
    m = _LEAD_NUM_RE.match(_limpar(el.get_text(" ")))
    if m:
        return int(m.group(1)), _limpar(m.group(2))
    return None


def _dedup(pares: list[tuple[int, str]]) -> list[tuple[int, str]]:
    vistos: dict[int, str] = {}
    for n, t in pares:
        if t and n not in vistos:
            vistos[n] = t
    return sorted(vistos.items())


def _por_seletor(soup: BeautifulSoup, cfg: TranslationConfig) -> list[tuple[int, str]]:
    pares = []
    for el in soup.select(cfg.verse_selector):
        par = _num_e_texto(el, cfg)
        if par:
            pares.append(par)
    return _dedup(pares)


def _por_atributos(soup: BeautifulSoup) -> list[tuple[int, str]]:
    pares = []
    for el in soup.find_all(True):
        if any(el.has_attr(a) for a in _ATTR_NUM) or _ID_RE.match(el.get("id", "") or ""):
            par = _num_e_texto(el)
            if par:
                pares.append(par)
    return _dedup(pares)


def _por_classes(soup: BeautifulSoup) -> list[tuple[int, str]]:
    pares = []
    for el in soup.find_all(class_=_CLASS_RE):
        par = _num_e_texto(el)
        if par:
            pares.append(par)
    return _dedup(pares)


def _por_texto_corrido(soup: BeautifulSoup) -> list[tuple[int, str]]:
    """Último recurso: linhas de texto que começam com o número do versículo."""
    pares = []
    for linha in soup.get_text("\n").splitlines():
        m = _LEAD_NUM_RE.match(linha)
        if m:
            pares.append((int(m.group(1)), _limpar(m.group(2))))
    return _dedup(pares)
