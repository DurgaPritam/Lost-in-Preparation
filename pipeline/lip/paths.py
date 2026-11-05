from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_SOURCES = ROOT / "config" / "sources.toml"
RAW_MANIFEST = ROOT / "data" / "raw" / "manifest.json"
INTERIM = ROOT / "data" / "interim"
SITE_DATA = ROOT / "site-data"


def load_sources() -> list[dict]:
    with CONFIG_SOURCES.open("rb") as fh:
        return tomllib.load(fh)["source"]
