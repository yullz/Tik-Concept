"""Counterfactual short-form video pipeline.

Stages: validate → lint → promptsheet → (keyframes, motion via Higgsfield) → tts → plan →
assemble → qc → metadata → bundle. See docs/04-production-pipeline.md and RUNBOOK.md.
"""
__version__ = "0.1.0"
