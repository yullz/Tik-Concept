"""Paths, environment and the style bible."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EPISODES_DIR = ROOT / "episodes"
RENDERS_DIR = ROOT / "renders"
STYLES_DIR = ROOT / "styles"
ASSETS_DIR = ROOT / "assets"
DOCS_DIR = ROOT / "docs"


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader (no dependency). Existing env vars win."""
    path = path or ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env(name: str, default: str | None = None) -> str | None:
    load_dotenv()
    return os.environ.get(name, default)


def load_style(name: str = "counterfact-v1") -> dict:
    path = STYLES_DIR / f"{name}.yaml"
    with path.open() as f:
        return yaml.safe_load(f)


def render_dir(episode_id: str) -> Path:
    d = RENDERS_DIR / episode_id
    for sub in ("keyframes", "clips", "audio", "publish"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d
