"""Explicit operator ingestion or bounded query; never executes corpus instructions."""

import argparse
import json
from .engine import answer, connect, ingest


def main():
    p = argparse.ArgumentParser()
    p.add_argument("operation", choices=("ingest", "query"))
    p.add_argument("--database", default=".local/index.sqlite")
    p.add_argument("--corpus", default="knowledge")
    p.add_argument("--query", default="How is approval bound to a proposal?")
    args = p.parse_args()
    if args.operation == "ingest":
        result = ingest(args.corpus, args.database)
    else:
        with connect(args.database) as db:
            result = answer(db, args.query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
