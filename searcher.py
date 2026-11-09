"""Reads queries from the console, searches the index and prints the ranked results.

Usage:  python searcher.py <index-directory>

Query syntax:
    name <terms>       e.g.  name report        name "machine learning"
    content <terms>    e.g.  content learning   content "entity resolution"
    quit
Several terms are combined with OR (OrGroup), so documents matching MORE terms rank higher
(Whoosh would use AND by default). Quotes "..." = phrase query.
"""
import sys

from whoosh import index
from whoosh.qparser import QueryParser, OrGroup

from analyzers import schema

TOP_K = 10


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python searcher.py <index-directory>")
    ix = index.open_dir(sys.argv[1])

    with ix.searcher() as searcher:            # default scoring: BM25F
        print(f"Index opened: {searcher.doc_count()} documents.")
        print('Syntax: name <terms> | content <terms> | quit   (use "..." for phrases)')

        while True:
            try:
                line = input("> ").strip()
            except EOFError:                   # e.g. when queries are piped from a file
                break
            if not line:
                continue
            if line.lower() == "quit":
                break

            parts = line.split(None, 1)
            field = parts[0].lower()
            if len(parts) < 2 or field not in ("name", "content"):
                print("Invalid query. Start with 'name' or 'content'.")
                continue

            # The parser uses the analyzer of that field -> the query is normalised like the index.
            parser = QueryParser(field, schema=ix.schema, group=OrGroup)
            query = parser.parse(parts[1])
            results = searcher.search(query, limit=TOP_K)

            print("Query parsed as:", query)
            print(f"{len(results)} result(s)")
            for rank, hit in enumerate(results, start=1):
                print(f"  {rank:2d}. {hit['name']:<30} score={hit.score:.3f}")


if __name__ == "__main__":
    main()
