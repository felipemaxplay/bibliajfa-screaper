"""Tabela dos 66 livros da Bíblia (protestante) com número de capítulos."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    num: int
    nome: str
    capitulos: int

    @property
    def slug(self) -> str:
        texto = unicodedata.normalize("NFKD", self.nome)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return "-".join(texto.lower().split())

    @property
    def testamento(self) -> str:
        """'O' para Antigo Testamento, 'N' para Novo Testamento."""
        return "O" if self.num <= 39 else "N"

    @property
    def pasta(self) -> str:
        return f"{self.num:02d}-{self.slug}"


_LIVROS = [
    ("Gênesis", 50), ("Êxodo", 40), ("Levítico", 27), ("Números", 36),
    ("Deuteronômio", 34), ("Josué", 24), ("Juízes", 21), ("Rute", 4),
    ("1 Samuel", 31), ("2 Samuel", 24), ("1 Reis", 22), ("2 Reis", 25),
    ("1 Crônicas", 29), ("2 Crônicas", 36), ("Esdras", 10), ("Neemias", 13),
    ("Ester", 10), ("Jó", 42), ("Salmos", 150), ("Provérbios", 31),
    ("Eclesiastes", 12), ("Cantares", 8), ("Isaías", 66), ("Jeremias", 52),
    ("Lamentações", 5), ("Ezequiel", 48), ("Daniel", 12), ("Oseias", 14),
    ("Joel", 3), ("Amós", 9), ("Obadias", 1), ("Jonas", 4),
    ("Miqueias", 7), ("Naum", 3), ("Habacuque", 3), ("Sofonias", 3),
    ("Ageu", 2), ("Zacarias", 14), ("Malaquias", 4),
    ("Mateus", 28), ("Marcos", 16), ("Lucas", 24), ("João", 21),
    ("Atos", 28), ("Romanos", 16), ("1 Coríntios", 16), ("2 Coríntios", 13),
    ("Gálatas", 6), ("Efésios", 6), ("Filipenses", 4), ("Colossenses", 4),
    ("1 Tessalonicenses", 5), ("2 Tessalonicenses", 3), ("1 Timóteo", 6),
    ("2 Timóteo", 4), ("Tito", 3), ("Filemom", 1), ("Hebreus", 13),
    ("Tiago", 5), ("1 Pedro", 5), ("2 Pedro", 3), ("1 João", 5),
    ("2 João", 1), ("3 João", 1), ("Judas", 1), ("Apocalipse", 22),
]

BOOKS: list[Book] = [Book(i, nome, cap) for i, (nome, cap) in enumerate(_LIVROS, 1)]

assert len(BOOKS) == 66
assert sum(b.capitulos for b in BOOKS) == 1189


def parse_book_range(spec: str | None) -> list[Book]:
    """Interpreta '1', '1-5' ou '1,3,40-42'. None devolve todos os livros."""
    if not spec:
        return list(BOOKS)
    nums: set[int] = set()
    for parte in spec.split(","):
        parte = parte.strip()
        if "-" in parte:
            ini, fim = parte.split("-", 1)
            nums.update(range(int(ini), int(fim) + 1))
        elif parte:
            nums.add(int(parte))
    return [b for b in BOOKS if b.num in nums]
