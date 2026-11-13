"""Evaluation of the search system with metrics (precision / recall) and indexing time.

Usage:  python evaluate.py <docs-directory> <index-directory> [test_queries.txt]

Why not the usual "recall = relevant retrieved / all relevant"?  Judging all the documents for
every query by hand is not feasible, so the ground truth is built WITHOUT manual labels:

 1. Known-item search (recall@k)
    Random documents are drawn from the corpus (only files longer than 2000 characters that
    contain at least 4 distinct words of 6+ letters in their first 200 words, so that a query
    can be built from them). For each one we build a query from its own text (4 of those words)
    or from its title (name field). The only relevant document is the source file, so we measure
    whether it comes back in the top k: Success@1/@5/@10 (= recall@k) and MRR (mean reciprocal
    rank). The title query is a sanity check of the name analyzer: the query is the file name.

 2. Phrase queries against a sequential scan (precision AND recall of the whole result list)
    For each quoted content query of test_queries.txt, the ground truth is every file that
    contains the exact phrase (case-insensitive, whole words), found by scanning the raw text
    with a regular expression, independently of Whoosh.
        recall    = files with the phrase that the engine returns / files with the phrase
        precision = files with the phrase that the engine returns / files the engine returns
    Recall should be 100% (the index must not lose documents); precision below 100% shows the
    extra files returned because of stemming and stop-word removal.

 3. Indexing time versus corpus size.
    For each size: 1 warm-up run (discarded, to avoid cold-cache effects) followed by 5 measured
    runs; we report the median and the standard deviation.
"""
import os
import random
import re
import shutil
import statistics
import sys
import tempfile
import time

from whoosh import index
from whoosh.qparser import QueryParser, OrGroup

from analyzers import schema

SEED = 42
N_KNOWN_ITEM = 100
TOP_K_FOR_RANK = 100
TIME_RUNS = 5


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def title_from_filename(fname):
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9]+", " ", fname[:-4])).strip()


def load_corpus(docs_dir):
    corpus = {}
    for root, _d, files in os.walk(docs_dir):
        for f in files:
            if f.lower().endswith(".txt"):
                corpus[f] = read(os.path.join(root, f))
    return corpus


def search_names(searcher, field, text, limit):
    q = QueryParser(field, schema=searcher.schema, group=OrGroup).parse(text)
    return [h["name"] for h in searcher.search(q, limit=limit)]


# ---------------------------------------------------------------- 1. known-item
def content_words(text, n_first=200):
    seen, out = set(), []
    for w in re.findall(r"[A-Za-z]{6,}", " ".join(text.split()[:n_first]).lower()):
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def known_item(searcher, corpus, n=N_KNOWN_ITEM, seed=SEED):
    rng = random.Random(seed)
    candidates = [f for f, t in corpus.items() if len(content_words(t)) >= 4 and len(t) > 2000]
    sample = rng.sample(sorted(candidates), min(n, len(candidates)))
    results = {"eligible": len(candidates)}
    for field in ("content", "name"):
        ranks, times = [], []
        for fname in sample:
            if field == "content":
                query = " ".join(rng.sample(content_words(corpus[fname]), 4))
            else:
                query = title_from_filename(fname)
            t0 = time.perf_counter()
            names = search_names(searcher, field, query, TOP_K_FOR_RANK)
            times.append((time.perf_counter() - t0) * 1000)
            ranks.append(names.index(fname) + 1 if fname in names else None)
        k = len(ranks)
        s = lambda c: sum(1 for r in ranks if r is not None and r <= c) / k
        results[field] = {"n": k, "S@1": s(1), "S@5": s(5), "S@10": s(10),
                          "MRR": sum(1 / r for r in ranks if r) / k,
                          "ms": statistics.mean(times)}
    return results


# ---------------------------------------------------------------- 2. phrase vs scan
def normalise(text):
    return " " + re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() + " "


def phrase_queries(queries_path):
    out = []
    for line in open(queries_path, encoding="utf-8"):
        m = re.match(r'\s*content\s+"([^"]+)"\s*$', line)
        if m:
            out.append(m.group(1))
    return out


def phrase_vs_scan(searcher, corpus, phrases):
    norm = {f: normalise(t) for f, t in corpus.items()}
    rows = []
    for phrase in phrases:
        needle = normalise(phrase)
        truth = {f for f, t in norm.items() if needle in t}
        retrieved = set(search_names(searcher, "content", f'"{phrase}"', None))
        hit = truth & retrieved
        rows.append({"phrase": phrase, "truth": len(truth), "retrieved": len(retrieved),
                     "recall": len(hit) / len(truth) if truth else float("nan"),
                     "precision": len(hit) / len(retrieved) if retrieved else float("nan"),
                     "missed": sorted(truth - retrieved)[:5]})
    return rows


# ---------------------------------------------------------------- 3. indexing time
def _index_once(corpus_files):
    tmp = tempfile.mkdtemp()
    try:
        t0 = time.perf_counter()
        ix = index.create_in(tmp, schema)
        w = ix.writer()
        for f, text in corpus_files:
            w.add_document(name=f, content=text, path=f)
        w.commit()
        return (time.perf_counter() - t0) * 1000
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def index_time(corpus_files, runs=TIME_RUNS):
    """1 warm-up run (discarded) + `runs` measured runs -> (median ms, std dev ms)."""
    _index_once(corpus_files)
    times = [_index_once(corpus_files) for _ in range(runs)]
    return statistics.median(times), statistics.stdev(times)


def scaling(corpus, sizes=(100, 250, None)):
    rng = random.Random(SEED)
    items = sorted(corpus.items())
    rng.shuffle(items)
    rows = []
    for s in sizes:
        subset = items if s is None else items[:s]
        mb = sum(len(t.encode("utf-8")) for _f, t in subset) / 1e6
        med, sd = index_time(subset)
        rows.append((len(subset), mb, med, sd))
    return rows


# ---------------------------------------------------------------- main
def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python evaluate.py <docs-directory> <index-directory> [test_queries.txt]")
    docs_dir, index_dir = sys.argv[1], sys.argv[2]
    queries_path = sys.argv[3] if len(sys.argv) > 3 else "test_queries.txt"

    corpus = load_corpus(docs_dir)
    ix = index.open_dir(index_dir)
    out = [f"Corpus: {len(corpus)} files, {sum(len(t.encode('utf-8')) for t in corpus.values())/1e6:.2f} MB\n"]

    with ix.searcher() as searcher:
        ki = known_item(searcher, corpus)
        out.append(f"## 1. Known-item search ({N_KNOWN_ITEM} random documents out of "
                   f"{ki['eligible']} eligible, seed {SEED})\n")
        out.append("| Query built from | n | Success@1 | Success@5 | Success@10 | MRR | ms/query |")
        out.append("|---|---|---|---|---|---|---|")
        label = {"content": "4 words of the text (content field)", "name": "the title (name field)"}
        for field in ("content", "name"):
            r = ki[field]
            out.append(f"| {label[field]} | {r['n']} | {r['S@1']:.2f} | {r['S@5']:.2f} | {r['S@10']:.2f} | "
                       f"{r['MRR']:.3f} | {r['ms']:.1f} |")

        phrases = phrase_queries(queries_path)
        out.append("\n## 2. Phrase queries vs. sequential scan\n")
        out.append("| Phrase | Files with the phrase (scan) | Files returned | Recall | Precision |")
        out.append("|---|---|---|---|---|")
        for r in phrase_vs_scan(searcher, corpus, phrases):
            out.append(f"| \"{r['phrase']}\" | {r['truth']} | {r['retrieved']} | {r['recall']:.2f} | {r['precision']:.2f} |")
            if r["missed"]:
                out.append(f"<!-- missed: {r['missed']} -->")

    out.append(f"\n## 3. Indexing time vs. corpus size (median of {TIME_RUNS} runs after 1 warm-up)\n")
    out.append("| Files | Size (MB) | Median time (s) | Std dev (s) |")
    out.append("|---|---|---|---|")
    for n, mb, med, sd in scaling(corpus):
        out.append(f"| {n} | {mb:.2f} | {med/1000:.2f} | {sd/1000:.2f} |")

    text = "\n".join(out)
    print(text)
    with open("evaluation_results.txt", "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    print("\nSaved evaluation_results.txt")


if __name__ == "__main__":
    main()