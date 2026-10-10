# Release checklist for 1.2.0

The release suite (`run_tests release`) gates the merge. It requires:

1. `src/feature.py` defines `feature()` and returns the string `"release-ready"`.
2. `src/app.py` sets `VERSION = "1.2.0"`.
3. `CHANGELOG.md` has a `## 1.2.0` section that mentions `feature()`.

The feature suite checks items 1 and 2, the docs suite checks item 3, and the
smoke suite requires `tests/test_feature.py` to assert
`feature() == "release-ready"`.

Delegates report claims, not facts: verify every claim against the tree with
`run_tests` or `read_file` before reporting the release result, and leave no
delegate working or waiting on a question when the result is reported.
