"""Indexes every .txt file of a directory (recursively) with two fields: name and content.

Usage:  python indexer.py <docs-directory> <index-directory>
"""
import os
import sys
import time

from whoosh import index

from analyzers import schema


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, "dataset_wikipedia")
    index_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base_dir, "index")

    os.makedirs(index_dir, exist_ok=True)
    start = time.perf_counter()

    # create_in ERASES any previous index in that folder, so every run starts from scratch
    ix = index.create_in(index_dir, schema)
    writer = ix.writer()

    count = 0
    total_bytes = 0
    for root, _dirs, files in os.walk(docs_dir):
        for fname in files:
            if not fname.lower().endswith(".txt"):
                continue
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            writer.add_document(name=fname, content=text, path=os.path.abspath(path))
            count += 1
            total_bytes += len(text.encode("utf-8"))

    writer.commit()                      # writes the index to disk
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"Indexed {count} files ({total_bytes / 1e6:.2f} MB) in {elapsed_ms:.1f} ms")


if __name__ == "__main__":
    main()
