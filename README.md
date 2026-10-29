# bibliajfa-screaper

Scraper em Python que extrai o texto completo da Bíblia do site [bibliajfa.com.br](https://bibliajfa.com.br/app/) e salva em **JSON estruturado** e em uma **árvore de arquivos TXT**. O escopo inicial é a tradução **NAA**; a arquitetura permite adicionar outras (ARA, NVI, NTLH...) apenas alterando a configuração.

> Respeite os termos de uso do site e os direitos autorais das traduções. Use os dados para fins pessoais e de estudo, e mantenha os delays configurados para não sobrecarregar o servidor.

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

Os comandos são executados a partir da raiz do projeto, com `PYTHONPATH=src` (ou `set PYTHONPATH=src` no Windows).

### 1. Inspecionar o site (primeira vez)

Descobre se o site usa uma API JSON interna ou HTML puro:

```bash
python scripts/inspect_site.py https://bibliajfa.com.br/app/naa/01O/1
```

Se houver API, preencha `api_url_template` em `src/bibliajfa_scraper/config.py`. Se o HTML precisar de seletores específicos, preencha `verse_selector`, `verse_number_selector` e `verse_text_selector`.

### 2. Rodar o scraper

```bash
PYTHONPATH=src python -m bibliajfa_scraper scrape --translation NAA
```

Opções úteis:

```bash
# apenas Gênesis a Levítico (teste rápido)
PYTHONPATH=src python -m bibliajfa_scraper scrape -t NAA --books 1-3

# delays customizados (segundos)
PYTHONPATH=src python -m bibliajfa_scraper scrape -t NAA --min-delay 2 --max-delay 4
```

O resultado vai para `data/json/naa.json`. O progresso é salvo ao fim de cada livro; se interromper, rode o mesmo comando novamente e a extração continua de onde parou (use `--no-resume` para recomeçar).

Formato de cada registro:

```json
{ "traducao": "NAA", "livro_num": 1, "livro_nome": "Gênesis", "capitulo": 1, "versiculo": 1, "texto": "..." }
```

### 3. Exportar para TXT

```bash
PYTHONPATH=src python -m bibliajfa_scraper export --translation NAA
```

Gera `data/txt/NAA/01-genesis/01.txt`, `02.txt`, ... com um versículo por linha:

```
1 No princípio...
2 A terra era sem forma e vazia...
```

## Cortesia de rede

- Delay aleatório entre requisições (padrão: 1 a 3 segundos).
- Retry com backoff exponencial para erros de rede e HTTP 408/425/429/5xx, respeitando `Retry-After`.
- Gravação atômica do JSON e retomada automática.

## Adicionando novas traduções

Edite `TRANSLATIONS` em `src/bibliajfa_scraper/config.py`:

```python
"ARA": TranslationConfig(codigo="ARA", slug="ara"),
```

Se a nova tradução tiver URL, API ou estrutura HTML diferente, ajuste `url_template`, `api_url_template` e os seletores na própria entrada. Depois:

```bash
PYTHONPATH=src python -m bibliajfa_scraper scrape -t ARA
PYTHONPATH=src python -m bibliajfa_scraper export -t ARA
```

## Estrutura do projeto

```
bibliajfa-screaper/
├── src/bibliajfa_scraper/
│   ├── books.py        # 66 livros e capítulos
│   ├── config.py       # configuração por tradução
│   ├── http_client.py  # delays, retry e backoff
│   ├── parser.py       # JSON e HTML para versículos
│   ├── scraper.py      # orquestração e JSON
│   ├── exporter.py     # JSON para árvore TXT
│   └── cli.py          # linha de comando
├── scripts/inspect_site.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Nota sobre IA

O desenvolvimento deste projeto contou com o auxílio de Inteligência Artificial.

## Licença

[MIT](LICENSE)
