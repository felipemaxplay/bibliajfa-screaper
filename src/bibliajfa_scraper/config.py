"""Configuração das traduções. Para adicionar uma nova, basta incluir uma entrada em TRANSLATIONS."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .books import Book

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"


@dataclass
class TranslationConfig:
    codigo: str  # ex.: "NAA" (usado nos arquivos e no JSON)
    slug: str  # ex.: "naa" (usado na URL)

    # Modelo de URL da página HTML. Placeholders: {slug}, {book_code}, {chapter}
    url_template: str = "https://bibliajfa.com.br/app/{slug}/{book_code}/{chapter}"

    # Se a inspeção encontrar uma API JSON, preencha o modelo (mesmos placeholders).
    api_url_template: str | None = None

    # Estilo do código do livro na URL:
    #   "global":      01O..39O, 40N..66N  (número global + testamento)
    #   "testamento":  01O..39O, 01N..27N  (número dentro do testamento)
    book_code_style: str = "global"

    # Seletores CSS. Padrão baseado no HTML do site: cada versículo é um
    # <blockquote id="verse-N"> com o número dentro de um <sup>.
    # Se vazios, o parser usa heurísticas.
    verse_selector: str | None = "blockquote[id^='verse-']"
    verse_number_selector: str | None = "sup"
    verse_text_selector: str | None = None

    # Cortesia de rede
    min_delay: float = 1.0
    max_delay: float = 3.0
    max_retries: int = 5
    backoff_base: float = 2.0
    timeout: float = 30.0

    headers: dict[str, str] = field(default_factory=lambda: {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 bibliajfa-scraper/0.1"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    })

    def book_code(self, book: Book) -> str:
        if self.book_code_style == "testamento":
            num = book.num if book.num <= 39 else book.num - 39
        else:
            num = book.num
        return f"{num:02d}{book.testamento}"

    def page_url(self, book: Book, chapter: int) -> str:
        return self.url_template.format(
            slug=self.slug, book_code=self.book_code(book), chapter=chapter
        )

    def api_url(self, book: Book, chapter: int) -> str | None:
        if not self.api_url_template:
            return None
        return self.api_url_template.format(
            slug=self.slug, book_code=self.book_code(book), chapter=chapter,
            book_num=book.num,
        )

    @property
    def json_path(self) -> Path:
        return DATA_DIR / "json" / f"{self.codigo.lower()}.json"

    @property
    def txt_dir(self) -> Path:
        return DATA_DIR / "txt" / self.codigo.upper()


TRANSLATIONS: dict[str, TranslationConfig] = {
    "NAA": TranslationConfig(codigo="NAA", slug="naa"),
    "ARA": TranslationConfig(codigo="ARA", slug="ara"),
    "NVI": TranslationConfig(codigo="NVI", slug="nvi"),
    "NTLH": TranslationConfig(codigo="NTLH", slug="ntlh"),
}


def get_translation(codigo: str) -> TranslationConfig:
    chave = codigo.upper()
    if chave not in TRANSLATIONS:
        validas = ", ".join(sorted(TRANSLATIONS))
        raise SystemExit(f"Tradução desconhecida: {codigo}. Disponíveis: {validas}")
    return TRANSLATIONS[chave]
