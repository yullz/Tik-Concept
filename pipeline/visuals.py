"""Higgsfield adapters.

Two routes:
  * MCP route (verified): `pipeline promptsheet` writes keyframe_batches.json whose entries are
    the exact `requests` arrays for generate_image_batch; `pipeline motionbatch` does the same
    for generate_video_batch once keyframes are selected. The executor runs the MCP tools, waits
    with jobs_wait, and calls `pipeline ingest` with a {shot: url} map.
  * REST route (endpoint paths configurable in .env, unverified from this container).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .config import env, load_style, render_dir
from .prompts import batch_requests
from .spec import Episode


def write_motion_batches(ep: Episode, keyframe_jobs: dict[str, str], style_name: str = "counterfact-v1") -> Path:
    rdir = render_dir(ep.id)
    sheet = json.loads((rdir / "promptsheet.json").read_text())
    batches = batch_requests(sheet, "motion", keyframe_jobs=keyframe_jobs, style_name=style_name)
    out = rdir / "motion_batches.json"
    out.write_text(json.dumps(batches, indent=2))
    return out


def ingest(ep: Episode, mapping: dict[str, str], kind: str) -> list[Path]:
    """Download result URLs into keyframes/ or clips/. mapping: {"shot-01-a": url} or {"shot-01": url}."""
    import requests

    rdir = render_dir(ep.id)
    sub = "keyframes" if kind == "keyframes" else "clips"
    saved = []
    for name, url in mapping.items():
        ext = ".png" if kind == "keyframes" else ".mp4"
        if kind == "keyframes" and any(url.lower().split("?")[0].endswith(e) for e in (".jpg", ".jpeg", ".webp")):
            ext = "." + url.lower().split("?")[0].rsplit(".", 1)[-1]
        dst = rdir / sub / f"{name}{ext}"
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        dst.write_bytes(r.content)
        saved.append(dst)
    return saved


class HiggsfieldREST:
    """Thin REST client. Endpoint templates come from .env so they can be corrected without code changes."""

    def __init__(self):
        self.base = env("HIGGSFIELD_BASE_URL", "https://platform.higgsfield.ai").rstrip("/")
        self.key = env("HIGGSFIELD_API_KEY")
        self.secret = env("HIGGSFIELD_API_SECRET")
        self.t2i = env("HIGGSFIELD_T2I_PATH", "/v1/text2image/{model}")
        self.i2v = env("HIGGSFIELD_I2V_PATH", "/v1/image2video/{model}")
        self.status = env("HIGGSFIELD_STATUS_PATH", "/v1/requests/{request_id}")
        if not (self.key and self.secret):
            raise SystemExit("HIGGSFIELD_API_KEY and HIGGSFIELD_API_SECRET are required for the REST route")

    def _headers(self):
        return {"hf-api-key": self.key, "hf-secret": self.secret, "Content-Type": "application/json"}

    def submit(self, path_tpl: str, model: str, params: dict) -> str:
        import requests
        url = self.base + path_tpl.format(model=model)
        r = requests.post(url, headers=self._headers(), json={"params": params}, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data.get("request_id") or data.get("id")

    def wait(self, request_id: str, timeout_s: int = 900) -> dict:
        import requests
        url = self.base + self.status.format(request_id=request_id)
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            r = requests.get(url, headers=self._headers(), timeout=30)
            r.raise_for_status()
            data = r.json()
            if data.get("status") in {"completed", "failed", "nsfw", "canceled"}:
                return data
            time.sleep(5)
        raise TimeoutError(request_id)


def rest_keyframes(ep: Episode, style_name: str = "counterfact-v1") -> dict[str, str]:
    client = HiggsfieldREST()
    style = load_style(style_name)
    rdir = render_dir(ep.id)
    batches = json.loads((rdir / "keyframe_batches.json").read_text())
    results = {}
    for batch in batches:
        ids = {req["index"]: client.submit(client.t2i, style["keyframe_model"], req["params"]) for req in batch}
        for idx, rid in ids.items():
            data = client.wait(rid)
            shot_i, variant = divmod(idx, 10)
            name = f"shot-{shot_i:02d}-{'a' if variant == 1 else 'b'}"
            url = (data.get("images") or [{}])[0].get("url") or data.get("result_url") or ""
            if url:
                results[name] = url
    (rdir / "keyframe_results.json").write_text(json.dumps(results, indent=2))
    ingest(ep, results, "keyframes")
    return results
