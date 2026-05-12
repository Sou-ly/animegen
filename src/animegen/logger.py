import logging
import sys
from pathlib import Path

_initialized = False


def setup(log_dir: Path, chapter: int) -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    log_file = log_dir / f"chapter_{chapter}.log"
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(sh)


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)
