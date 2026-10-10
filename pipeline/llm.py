"""The Claude Opus 5.5 stage: research sheets, scripts, metadata, localisations.

Design is Fable 5.1's; execution is Opus 5.5's (docs/08-model-policy.md). Output is YAML inside a
```yaml fence, parsed, validated and linted; failures are fed back for up to three rewrite rounds.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .config import DOCS_DIR, STYLES_DIR
from .lint import lint_episode
from .spec import episode_from_dict, validate

MODEL = "claude-opus-5-5"


def _client():
    try:
        import anthropic  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise SystemExit("pip install anthropic  (the Opus 5.5 stage needs the SDK)") from e
    return anthropic.Anthropic()


def system_prompt() -> list[dict]:
    """Charter + beat sheet + style + voice docs as a cached, stable prefix."""
    parts = []
    for name in ("00-anti-slop-charter.md", "02-format-beat-sheet.md", "05-visual-style-and-prompt-library.md", "06-voice-and-sound.md"):
        parts.append((DOCS_DIR / name).read_text())
    parts.append("STYLE BIBLE YAML:\n" + (STYLES_DIR / "counterfact-v1.yaml").read_text())
    parts.append((Path(__file__).parent / "prompts" / "episode_schema.md").read_text())
    text = "\n\n---\n\n".join(parts)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def _extract_yaml(text: str) -> dict:
    m = re.search(r"```ya?ml\s*(.*?)```", text, re.S)
    body = m.group(1) if m else text
    return yaml.safe_load(body)


def _ask(client, user_text: str, effort: str = "high") -> str:
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=system_prompt(),
        output_config={"effort": effort},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": user_text}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise SystemExit(f"model declined: {getattr(msg, 'stop_details', None)}")
    return "".join(b.text for b in msg.content if b.type == "text")


def write_episode(brief: str, out_path: Path, rounds: int = 3) -> Path:
    """Research + script + shots in one YAML, iterated against the linter."""
    client = _client()
    ask = (f"BRIEF:\n{brief}\n\nWrite the complete episode YAML (schema in the system prompt). Research first: the hinge "
           f"must be a real, dated event with at least two sources. Return ONLY one ```yaml block.")
    text = _ask(client, ask)
    for r in range(rounds):
        data = _extract_yaml(text)
        ep = episode_from_dict(data)
        errs, warns = validate(ep)
        lerrs, lwarns = lint_episode(ep)
        problems = errs + lerrs
        if not problems:
            out_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))
            return out_path
        feedback = "\n".join(f"- {p}" for p in problems) + ("\n\nWarnings:\n" + "\n".join(f"- {w}" for w in warns + lwarns) if warns + lwarns else "")
        text = _ask(client, f"{ask}\n\nYour previous YAML failed validation. Fix every item and return the full YAML again:\n{feedback}\n\nPREVIOUS:\n{text}")
    raise SystemExit(f"episode still failing after {rounds} rounds; last problems:\n{feedback}")


def localize_episode(ep_path: Path, lang: str) -> Path:
    client = _client()
    src = Path(ep_path).read_text()
    text = _ask(client, f"Translate the narration (beats[].vo), cards, dilemma, pinned_comment and metadata of this episode YAML into {lang}. "
                        f"Keep ids, shots and prompts unchanged. Numbers stay spelled out in {lang}. Return ONLY the full ```yaml block.\n\n{src}", effort="medium")
    data = _extract_yaml(text)
    out = Path(ep_path).with_name(Path(ep_path).stem + f".{lang}.yaml")
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))
    return out
