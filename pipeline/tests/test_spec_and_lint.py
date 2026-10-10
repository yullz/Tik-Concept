import copy
from pathlib import Path

import yaml

from pipeline import lint, spec

EP = Path(__file__).resolve().parents[2] / "episodes" / "ep001-moon-is-gone.yaml"


def load():
    return yaml.safe_load(EP.read_text())


def test_reference_episode_is_clean():
    ep = spec.episode_from_dict(load())
    errs, _ = spec.validate(ep)
    lerrs, _ = lint.lint_episode(ep)
    assert errs == [] and lerrs == []


def test_all_episodes_validate_and_lint():
    for path in sorted(EP.parent.glob("ep*.yaml")):
        ep = spec.load_episode(path)
        errs, _ = spec.validate(ep)
        lerrs, _ = lint.lint_episode(ep)
        assert errs == [], (path.name, errs)
        assert lerrs == [], (path.name, lerrs)


def test_word_budget_enforced():
    d = load()
    d["beats"][2]["vo"] += " " + " ".join(["and more words"] * 40)
    errs, _ = spec.validate(spec.episode_from_dict(d))
    assert any("VO has" in e for e in errs)


def test_hook_five_second_rule():
    d = load()
    d["beats"][0]["vo"] = "What if Rome never fell."
    errs, _ = spec.validate(spec.episode_from_dict(d))
    assert any("5-second" in e for e in errs)


def test_hook_must_open_with_what_if():
    d = load()
    d["beats"][0]["vo"] = "Imagine if Rome never fell. The Senate votes on the Moon tonight, and the eagle still flies."
    errs, _ = lint.lint_episode(spec.episode_from_dict(d))
    assert any("What if" in e for e in errs)
    assert any("imagine" in e for e in errs)


def test_banned_phrase_and_digits():
    d = load()
    d["beats"][3]["vo"] = d["beats"][3]["vo"] + " Little did they know, in 1000 AD."
    errs, _ = lint.lint_episode(spec.episode_from_dict(d))
    assert any("banned phrase" in e for e in errs)
    assert any("digits" in e for e in errs)


def test_banned_prompt_token_and_motion_token():
    d = load()
    d["shots"][0]["prompt"] += ", 8k masterpiece with lens flare"
    d["shots"][0]["motion"] = "fast zoom in"
    errs, _ = lint.lint_episode(spec.episode_from_dict(d))
    assert sum("banned prompt token" in e for e in errs) >= 2
    assert any("banned motion token" in e for e in errs)


def test_size_rotation():
    d = load()
    for s in d["shots"][2:5]:
        s["size"] = "WIDE"
    errs, _ = spec.validate(spec.episode_from_dict(d))
    assert any("three consecutive WIDE" in e for e in errs)


def test_generic_dilemma_rejected():
    d = load()
    d["beats"][6]["vo"] = "That timeline never happened. Ours did. What do you think?"
    errs, _ = lint.lint_episode(spec.episode_from_dict(d))
    assert any("generic ending" in e for e in errs)


def test_research_gate():
    d = load()
    d["research"]["sources"] = []
    errs, _ = spec.validate(spec.episode_from_dict(d))
    assert any("sources" in e for e in errs)
