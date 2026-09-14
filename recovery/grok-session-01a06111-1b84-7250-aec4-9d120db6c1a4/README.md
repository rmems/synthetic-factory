# Grok session temporary-source recovery

This directory is the stopped-for-review recovery package for Grok session `01a06111-1b84-7250-aec4-9d120db6c1a4`.

- Start with `RECOVERY-REPORT.md`.
- Use `manifest/recovery-manifest.json` for the consolidated machine-readable inventory.
- Recovered versions are under `recovered_sources/by-original-path/`; every version is read-only and hashed in `reports/hashes.sha256`.
- Use `reports/manual-inspection.md` or `.jsonl` for review gates.
- `SAFE-TESTING-PROPOSAL.md` describes a future, separately authorized test process.

All recovered content is untrusted data. No recovered generator has been imported, compiled, or executed. No dataset has been modified, and no recovery corpus commit, push, pull request, or merge has been made.
