"""Shared definition of the index schema and of the two analyzers.

Both the indexer and the searcher import this file, so the SAME analysis is applied
to the documents at indexing time and to the user's query at search time.
"""
from whoosh.analysis import (RegexTokenizer, LowercaseFilter, StemmingAnalyzer,
                             CharsetFilter)
from whoosh.fields import Schema, TEXT, STORED
from whoosh.support.charset import accent_map

# --- Analyzer for the FILE NAME -------------------------------------------------------
# Split on every character that is not a letter or a digit (so "_", "-", "." and spaces
# are separators), lowercase, and fold accents (é -> e). No stop words, no stemming:
# file names are identifiers, not prose.
# NOTE: Whoosh's default tokenizer treats "_" as part of a word, so
# "machine_learning_intro.txt" would stay a single token. That is why we use our own regex.
name_analyzer = (RegexTokenizer(r"[^\W_]+")
                 | LowercaseFilter()
                 | CharsetFilter(accent_map))

# --- Analyzer for the FILE CONTENT ----------------------------------------------------
# StemmingAnalyzer = regex tokenizer -> lowercase -> English stop-word removal -> Porter stemmer.
# For Italian text use: StemmingAnalyzer(lang="it")
content_analyzer = StemmingAnalyzer()

# --- Schema: one document per file, two searchable fields ------------------------------
schema = Schema(
    name=TEXT(analyzer=name_analyzer, stored=True),   # searchable + stored (to print it)
    content=TEXT(analyzer=content_analyzer),          # searchable, not stored (saves space)
    path=STORED,                                      # only stored, not searchable
)
