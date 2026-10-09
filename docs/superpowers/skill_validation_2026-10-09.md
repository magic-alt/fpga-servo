# Project KiCad skill validation

Baseline request: continue AX7010 OCP repair on a topic branch and determine layout readiness.
Without project skill, the independent agent selected the obsolete `.sch`, dual `.lib` and `check_legacy_schematic.py` commands from the old AGENTS.md. It correctly identified their possible conflict but could not inspect files because the default sandbox helper failed. This is a reference-discovery gap, not a claim that actual hardware tests failed.

Correction: native source paths, fresh netlist validation commands, physical package checks and separate ERC/layout/fabrication gates in the project skill; root AGENTS updated to native commands. Forward test and validator results are recorded after execution.

Forward test passed: independent agent selected the actual native top, verified the topic branch, ran the five checks successfully, identified stale release-gate counts and correctly withheld layout-freeze approval. `quick_validate.py` returned `Skill is valid!`. The stale release notes have now been refreshed. This is a project reference skill; no behavior-shaping wording micro-test was needed.
