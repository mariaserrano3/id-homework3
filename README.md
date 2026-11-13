# Homework 3 – Indexing and searching .txt files with Whoosh

Course: Ingegneria dei dati 2026/2027 (Roma Tre) – Homework 3.

Search system for `.txt` files built on the [Whoosh](https://github.com/Sygil-Dev/whoosh-reloaded) library
(`whoosh-reloaded`, BM25F ranking). Each file becomes one document with two searchable fields, `name`
(file name) and `content` (file text), plus a stored, non-searchable `path`.

## Repository structure

| Path | Description |
|---|---|
| `analyzers.py` | Index schema and the two analyzers (shared by indexer, searcher and evaluation) |
| `indexer.py` | Builds the index and prints number of files, total size and indexing time |
| `searcher.py` | Interactive console search (top 10 results, BM25F) |
| `evaluate.py` | Evaluation: known-item search (Success@k, MRR), phrase queries vs. sequential scan (precision/recall), indexing time vs. corpus size |
| `txt_wikipedia.py` | Script used to build the corpus from Wikipedia (see "Dataset") |
| `dataset_wikipedia.zip` | The corpus: 500 English Wikipedia articles as `.txt` files (8 MB, CC BY-SA) |
| `test_queries.txt` | The 40 test queries |
| `results.txt` | Output of `searcher.py` on `test_queries.txt` |
| `evaluation_results.txt` | Output of `evaluate.py` (tables used in the report) |
| `requirements.txt` | Python dependencies |

## Setup

    pip install -r requirements.txt

(`wikipedia` is only needed to re-create the corpus with `txt_wikipedia.py`; the indexer, the searcher and
the evaluation need only `whoosh-reloaded`.)

## Dataset

`dataset_wikipedia.zip` contains the 500 files used in the report. `txt_wikipedia.py` builds a corpus like it:
for each of six seed topics (Computer science, Data engineering, Information retrieval, History of Rome,
Ancient Rome, Roman Empire) it runs a Wikipedia search, takes up to 120 titles and saves each article
as `<title>.txt` (non-alphanumeric characters replaced by `_`) until 500 files are reached. Disambiguation
pages and missing pages are skipped. Re-running it later may give slightly different files, because
Wikipedia changes; use the zip to reproduce the report.

    unzip dataset_wikipedia.zip          # creates the folder dataset_wikipedia/

## Run

Index the corpus (the index is rebuilt from scratch at every run):

    python indexer.py dataset_wikipedia index

Search interactively:

    python searcher.py index

Run all the test queries at once:

    python searcher.py index < test_queries.txt

(On Windows PowerShell use `Get-Content test_queries.txt | python searcher.py index` instead.)

Run the evaluation (it needs the index and takes a few minutes, because it re-indexes the corpus several
times to measure the time):

    python evaluate.py dataset_wikipedia index test_queries.txt

It prints the tables and saves them in `evaluation_results.txt`. Both `indexer.py` and `evaluate.py`
work with any other folder of `.txt` files, e.g. `python indexer.py "C:\path\to\my\txt\folder" index`.

## Query syntax

    name <terms>        e.g.  name report        name "machine learning"
    content <terms>     e.g.  content learning   content "entity resolution"
    quit

The first word selects the field (and the analyzer used to parse the query). Several terms are combined
with OR, so documents matching more terms rank higher. Terms in double quotes form a phrase query.

## Analyzers (short summary)

* `name`: regex tokenizer `[^\W_]+` (splits on every non-alphanumeric character, including `_`), lowercase,
  accent folding. No stop words and no stemming.
* `content`: `StemmingAnalyzer` (tokenizer, lowercase, English stop words, Porter stemmer).

The full motivation and the results are in the report.
