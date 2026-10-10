PY ?= python3
EP ?= episodes/ep001-moon-is-gone.yaml

.PHONY: help install test validate lint plan tts promptsheet assemble qc metadata dryrun all

help:
	@echo "make validate EP=episodes/epNNN.yaml   # schema + duration budget"
	@echo "make lint EP=...                        # anti-slop script linter"
	@echo "make promptsheet EP=...                 # keyframe + motion prompts (Higgsfield)"
	@echo "make tts EP=...                         # ElevenLabs VO + word timings"
	@echo "make plan EP=...                        # timeline / EDL from VO timings"
	@echo "make assemble EP=...                    # ffmpeg render (needs clips in renders/<ep>/clips)"
	@echo "make qc EP=...                          # technical QC + taste gate"
	@echo "make metadata EP=...                    # titles, captions, hashtags, pinned comment"
	@echo "make dryrun EP=...                      # full offline render with placeholder media"

install:
	$(PY) -m pip install -r requirements.txt

test:
	$(PY) -m pytest -q pipeline/tests

validate:
	$(PY) -m pipeline validate $(EP)
lint:
	$(PY) -m pipeline lint $(EP)
promptsheet:
	$(PY) -m pipeline promptsheet $(EP)
tts:
	$(PY) -m pipeline tts $(EP)
plan:
	$(PY) -m pipeline plan $(EP)
assemble:
	$(PY) -m pipeline assemble $(EP)
qc:
	$(PY) -m pipeline qc $(EP)
metadata:
	$(PY) -m pipeline metadata $(EP)
dryrun:
	$(PY) -m pipeline dryrun $(EP)
