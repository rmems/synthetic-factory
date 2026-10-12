# release-delegation

A two-file application (`src/app.py` and the `src/feature.py` the 1.2.0
release adds), its changelog, and the release checklist under `docs/`. Three
delegate roles work on it: an implementer, a tester, and a scribe. The
orchestrator briefs them, awaits their reports, and verifies every claim
against the tree before reporting the release result.
