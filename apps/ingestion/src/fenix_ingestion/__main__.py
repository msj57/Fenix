import asyncio
import logging
import sys
from pathlib import Path

from fenix_ingestion.pipeline import run


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    corpus_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus")
    if not corpus_root.is_dir():
        logging.error("El directorio de corpus no existe: %s", corpus_root)
        return 1
    return asyncio.run(run(corpus_root))


if __name__ == "__main__":
    raise SystemExit(main())
