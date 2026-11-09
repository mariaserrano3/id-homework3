# Homework 3 – Indexing and searching .txt files with Whoosh

Course: Ingegneria dei dati 2026/2027 (Roma Tre) – Homework 3.

Two Python programs built on the [Whoosh](https://github.com/Sygil-Dev/whoosh-reloaded) search library:

* `indexer.py` indexes every `.txt` file of a directory (recursively) with two fields: `name` and `content`.
* `searcher.py` reads queries from the console, searches the index and prints the ranked results.

## Repository structure

| Path | Description |
|---|---|
| `analyzers.py` | Index schema and the two analyzers (shared by the other scripts) |
| `indexer.py` | Builds the index and prints number of files, size and indexing time |
| `searcher.py` | Interactive console search |
| `test_queries.txt` | The 12 test queries used in the report |
| `data/` | Test corpus: 31 small English `.txt` files |
| `requirements.txt` | Python dependency (`whoosh-reloaded`) |

## Setup

    pip install -r requirements.txt

## Run

    python indexer.py data index
    python searcher.py index

Run all the test queries at once:

    python searcher.py index < test_queries.txt

(On Windows PowerShell use `Get-Content test_queries.txt | python searcher.py index` instead.)

`indexer.py` takes the documents directory and the index directory as arguments, so it also works with any other folder of `.txt` files:

    python indexer.py "C:\path\to\my\txt\folder" index

The index is rebuilt from scratch at every run.

## Query syntax

    name <terms>        e.g.  name report        name "machine learning"
    content <terms>     e.g.  content learning   content "entity resolution"
    quit

The first word selects the field (and the analyzer used to parse the query). Several terms are combined with OR, so documents matching more terms rank higher. Terms in double quotes form a phrase query.

## Analyzers (short summary)

* `name`: regex tokenizer splitting on every non-alphanumeric character, lowercase, accent folding. No stop words and no stemming.
* `content`: `StemmingAnalyzer` (tokenizer, lowercase, English stop words, Porter stemmer).

The full motivation is in the report.