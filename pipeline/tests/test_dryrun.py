import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EP = ROOT / "episodes" / "ep001-rome-never-fell.yaml"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_offline_dryrun_renders_and_passes_technical_qc():
    r = subprocess.run([sys.executable, "-m", "pipeline", "dryrun", str(EP)], cwd=ROOT, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stdout + r.stderr
    qc = json.loads((ROOT / "renders" / "ep001-rome-never-fell" / "qc.json").read_text())
    assert qc["pass"], qc
    assert 61 <= qc["duration"] <= 90
