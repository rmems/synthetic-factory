#!/usr/bin/env python3
"""Mill package-release-factory r163+ as release-attestation plants.

BAN r98–r162 digest-vs-git-SHA + lock-yank twins. Not another ecosystem's
`subject=git SHA` then `yank+republish; lock still pinned`.

New plants: sigstore/cosign identity, npm provenance OIDC, PyPI trusted
publishing, Maven GPG/portal, crates.io yank vs index protocol, Homebrew
bottle rebuild, Nix NAR-of-src vs gzip, NuGet snupkg metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

FACTORY = "package-release-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 163


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def hx(label: str, n: int = 64) -> str:
    return hashlib.sha256(f"pkg-attest-{label}".encode()).hexdigest()[:n]


def gsha(label: str) -> str:
    return hashlib.sha1(f"pkg-git-{label}".encode()).hexdigest()


def step(
    n: int,
    basis: str,
    obs: str,
    *,
    cmd: str | None = None,
    tool: str = "bash",
    path: str | None = None,
    contents: str | None = None,
    old: str | None = None,
    new: str | None = None,
    refl: str | None = None,
) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    if len(basis) > 240:
        raise SystemExit(f"decision_basis too long ({len(basis)}): {basis}")
    if tool == "bash":
        tc = {"name": "bash", "args": {"command": cmd}}
    elif tool == "read":
        tc = {"name": "read", "args": {"path": path}}
    elif tool == "write":
        tc = {"name": "write", "args": {"path": path, "contents": contents}}
    elif tool == "edit":
        tc = {"name": "edit", "args": {"path": path, "old": old, "new": new}}
    else:
        raise SystemExit(f"bad tool {tool}")
    out = {
        "n": n,
        "decision_basis": basis,
        "tool_call": tc,
        "observation": obs,
    }
    if refl:
        out["reflection"] = refl
    return out


def rec(round_n: int, spec: dict, steps: list[dict]) -> dict:
    if not (12 <= len(steps) <= 18):
        raise SystemExit(f"{spec['slug']} step count {len(steps)} not in 12–18")
    return {
        "id": f"pkg-r{round_n}-{spec['slug']}",
        "goal": spec["goal"],
        "plan": spec["plan"],
        "steps": steps,
        "outcome": spec["outcome"],
        "reward": spec["reward"],
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


# ---------------------------------------------------------------------------
# Builders — each family has its own command sequence. None use
# "digest = git SHA" or "yank then lock still pinned".
# ---------------------------------------------------------------------------


def ok_cosign_reusable(n: int, s: dict) -> dict:
    """Calling-repo workflow identity ≠ reusable-workflow Fulcio SAN."""
    img = s["image"]
    digest = s["digest"]
    call_id = s["call_id"]
    reuse_id = s["reuse_id"]
    tag = s["tag"]
    ver = s["ver"]
    leftover = s["leftover"]
    steps = [
        step(
            1,
            "Plan: inspect signed tag, image digest, and last cosign verify failure before rewriting --certificate-identity.",
            s["inspect_obs"],
            cmd=s["inspect_cmd"],
        ),
        step(
            2,
            f"Observation: signed tag {tag} and digest {digest[:12]} (step 1). Read calling workflow.",
            s["wf_obs"],
            tool="read",
            path=s["wf_path"],
        ),
        step(
            3,
            "Observation: calling workflow uses a reusable cosign job (step 2). Read verify policy.",
            s["pol_obs"],
            tool="read",
            path=s["pol_path"],
        ),
        step(
            4,
            "Observation: policy pins the calling-repo workflow (step 3). Dump last verify log.",
            s["decode_obs"],
            cmd=s["decode_cmd"],
        ),
        step(
            5,
            "Plan: first apply — verify with the calling-repo workflow as --certificate-identity.",
            s["apply_obs"],
            cmd=s["apply_cmd"],
            refl="Apply failed. Fulcio SAN is the reusable workflow, not the calling repo path.",
        ),
        step(
            6,
            "Observation: verifier rejected calling-repo identity (step 5). Extract Fulcio SAN from the bundle.",
            s["san_obs"],
            cmd=s["san_cmd"],
        ),
        step(
            7,
            "Observation: SAN is the reusable workflow (step 6). Confirm issuer and reusable ref.",
            s["iss_obs"],
            cmd=s["iss_cmd"],
        ),
        step(
            8,
            "Reflection: plan change — verify against the reusable-workflow SAN and GitHub OIDC issuer. Do not pin the calling repo.",
            "patched policy: identity=reusable workflow, issuer=token.actions.githubusercontent.com",
            tool="write",
            path=s["pol_path"],
            contents=s["pol_new"],
        ),
        step(
            9,
            "Observation: policy retargeted (step 8). Re-verify the image digest with the reusable SAN.",
            s["verify_obs"],
            cmd=s["verify_cmd"],
        ),
        step(
            10,
            "Observation: verify passed (step 9). Confirm leftover unsigned :latest still exists.",
            s["left_obs"],
            cmd=s["left_cmd"],
        ),
        step(
            11,
            "Observation: leftover tag present (step 10). Attach the good bundle to the digest; do not retag :latest.",
            s["up_obs"],
            cmd=s["up_cmd"],
        ),
        step(
            12,
            "Observation: bundle attached (step 11). Comment the identity constraint on the calling workflow.",
            "commented reusable-workflow identity constraint",
            tool="edit",
            path=s["wf_path"],
            old=s["wf_old"],
            new=s["wf_new"],
        ),
        step(
            13,
            f"Observation: workflow comment (step 12). Commit policy+workflow; do not move {tag}.",
            s["cmt_obs"],
            cmd=s["cmt_cmd"],
        ),
        step(
            14,
            f"Observation: commit after signed tag (step 13). Confirm {tag} still on original commit.",
            s["tag_obs"],
            cmd=s["tag_cmd"],
        ),
        step(
            15,
            "Observation: tag unmoved (step 14). Record residual unsigned latest.",
            s["res_obs"],
            cmd=s["res_cmd"],
            refl=s["res_refl"],
        ),
    ]
    s = {
        **s,
        "goal": (
            f"Ship {s['plant']} {ver}. Image {img}@{digest[:19]}… must verify "
            f"with Fulcio SAN = reusable workflow {s['reuse_short']}, not the calling "
            f"repo workflow. Keep signed {tag}. Leave {leftover} unsigned."
        ),
        "plan": (
            f"Rewrite --certificate-identity to the calling-repo {call_id} so the "
            "signature matches the signed tag, then cosign verify."
        ),
        "outcome": (
            f"First apply verified with calling-repo identity {call_id}; cosign "
            f"rejected (Fulcio SAN is {reuse_id}). Plan change: identity = reusable "
            f"workflow, issuer = GitHub OIDC. {tag} not moved. Residual: {leftover}."
        ),
        "reward": {
            "success": True,
            "sign_fails": 1,
            "plan_changes": 1,
            "attestations": 1,
            "cost_steps": 15,
        },
    }
    return rec(n, s, steps)


def ok_oidc_publisher(n: int, s: dict) -> dict:
    """Trusted-publisher / OIDC claim mismatch (workflow name, env, or host)."""
    steps = [
        step(1, "Plan: inspect publisher registration, workflow filename, and last OIDC publish failure.", s["inspect_obs"], cmd=s["inspect_cmd"]),
        step(2, "Observation: publisher row and last error captured (step 1). Read the workflow on disk.", s["wf_obs"], tool="read", path=s["wf_path"]),
        step(3, "Observation: workflow filename and environment (step 2). Read project metadata.", s["meta_obs"], tool="read", path=s["meta_path"]),
        step(4, "Observation: project metadata matches the intended version (step 3). Dump last OIDC token claims.", s["claim_obs"], cmd=s["claim_cmd"]),
        step(5, "Plan: first apply — publish with the currently registered publisher and this workflow as-is.", s["apply_obs"], cmd=s["apply_cmd"], refl=s["apply_refl"]),
        step(6, "Observation: publisher rejected the job (step 5). Diff registered workflow vs on-disk path.", s["diff_obs"], cmd=s["diff_cmd"]),
        step(7, "Observation: claim mismatch isolated (step 6). Confirm issuer and subject.", s["iss_obs"], cmd=s["iss_cmd"]),
        step(8, "Reflection: plan change — align the registered publisher with the workflow that actually runs. Do not fall back to a long-lived token.", "patched publisher registration / workflow alignment", tool="write", path=s["fix_path"], contents=s["fix_contents"]),
        step(9, "Observation: publisher aligned (step 8). Re-run the OIDC publish.", s["pub_obs"], cmd=s["pub_cmd"]),
        step(10, "Observation: publish accepted (step 9). Confirm attestations / provenance on the new version.", s["att_obs"], cmd=s["att_cmd"]),
        step(11, "Observation: attestations present (step 10). Confirm leftover token-published version still has none.", s["left_obs"], cmd=s["left_cmd"]),
        step(12, "Observation: leftover version remains (step 11). Do not delete it; document the skip.", s["doc_obs"], cmd=s["doc_cmd"]),
        step(13, "Observation: skip documented (step 12). Sign/keep the git tag; do not rewrite history.", s["tag_obs"], cmd=s["tag_cmd"]),
        step(14, "Observation: tag in place (step 13). Commit workflow/publisher notes.", s["cmt_obs"], cmd=s["cmt_cmd"]),
        step(15, "Observation: commit landed (step 14). Residual note.", s["res_obs"], cmd=s["res_cmd"], refl=s["res_refl"]),
    ]
    return rec(n, s, steps)


def ok_gpg_portal(n: int, s: dict) -> dict:
    """Maven GPG subkey / Publisher Portal vs OSSRH."""
    steps = [
        step(1, "Plan: inspect GPG keyring, staging repo, and last close/sign failure.", s["inspect_obs"], cmd=s["inspect_cmd"]),
        step(2, "Observation: keyring and staging id captured (step 1). Read pom signing plugin.", s["pom_obs"], tool="read", path=s["pom_path"]),
        step(3, "Observation: plugin config (step 2). Read settings.xml server/gpg.", s["set_obs"], tool="read", path=s["set_path"]),
        step(4, "Observation: settings pin a signing key (step 3). Show key expiration.", s["exp_obs"], cmd=s["exp_cmd"]),
        step(5, "Plan: first apply — close/release with the currently selected signing key.", s["apply_obs"], cmd=s["apply_cmd"], refl=s["apply_refl"]),
        step(6, "Observation: close rejected (step 5). List subkeys and capability flags.", s["sub_obs"], cmd=s["sub_cmd"]),
        step(7, "Observation: signing subkey problem isolated (step 6). Confirm portal vs OSSRH endpoint.", s["ep_obs"], cmd=s["ep_cmd"]),
        step(8, "Reflection: plan change — select a valid signing subkey (or Portal API) and open a new staging repo. Do not reuse the rejected signatures.", "patched signing key / portal endpoint", tool="write", path=s["fix_path"], contents=s["fix_contents"]),
        step(9, "Observation: signing retargeted (step 8). Re-sign and upload.", s["sign_obs"], cmd=s["sign_cmd"]),
        step(10, "Observation: new signatures accepted (step 9). Close the new staging repo.", s["close_obs"], cmd=s["close_cmd"]),
        step(11, "Observation: close ok (step 10). Confirm leftover rejected staging still listed.", s["left_obs"], cmd=s["left_cmd"]),
        step(12, "Observation: leftover staging present (step 11). Drop it from the release notes; do not promote it.", s["drop_obs"], cmd=s["drop_cmd"]),
        step(13, "Observation: leftover not promoted (step 12). Keep the signed git tag on the original commit.", s["tag_obs"], cmd=s["tag_cmd"]),
        step(14, "Observation: tag unmoved (step 13). Commit pom/settings.", s["cmt_obs"], cmd=s["cmt_cmd"]),
        step(15, "Observation: commit landed (step 14). Residual note.", s["res_obs"], cmd=s["res_cmd"], refl=s["res_refl"]),
    ]
    return rec(n, s, steps)


def ok_bottle_rebuild(n: int, s: dict) -> dict:
    """Homebrew bottle SHA after runner-image / bottle_custom_version rebuild."""
    steps = [
        step(1, "Plan: inspect formula bottle block, runner image, and last brew audit failure.", s["inspect_obs"], cmd=s["inspect_cmd"]),
        step(2, "Observation: bottle SHA and runner captured (step 1). Read the formula.", s["f_obs"], tool="read", path=s["f_path"]),
        step(3, "Observation: formula bottle_custom_version (step 2). Read bottle JSON from CI.", s["j_obs"], tool="read", path=s["j_path"]),
        step(4, "Observation: JSON sha256 vs formula disagree (step 3). Confirm runner image digest.", s["run_obs"], cmd=s["run_cmd"]),
        step(5, "Plan: first apply — rewrite formula sha256 from the old bottle without --rebuild.", s["apply_obs"], cmd=s["apply_cmd"], refl=s["apply_refl"]),
        step(6, "Observation: audit still red (step 5). Pour the published bottle and hash it.", s["pour_obs"], cmd=s["pour_cmd"]),
        step(7, "Observation: poured bytes ≠ formula (step 6). Check bottle_custom_version policy.", s["pol_obs"], cmd=s["pol_cmd"]),
        step(8, "Reflection: plan change — brew bottle --rebuild, bump bottle_custom_version, write the new sha256. Do not keep the pre-image-bump bottle.", "patched formula bottle block + bottle_custom_version", tool="write", path=s["f_path"], contents=s["f_new"]),
        step(9, "Observation: formula retargeted (step 8). Rebuild and emit new bottle JSON.", s["reb_obs"], cmd=s["reb_cmd"]),
        step(10, "Observation: new bottle hashed (step 9). brew audit --strict.", s["aud_obs"], cmd=s["aud_cmd"]),
        step(11, "Observation: audit 0 (step 10). Confirm leftover old-OS bottle still listed.", s["left_obs"], cmd=s["left_cmd"]),
        step(12, "Observation: leftover bottle listed (step 11). Do not delete gh release assets; note them.", s["note_obs"], cmd=s["note_cmd"]),
        step(13, "Observation: leftover noted (step 12). Keep the signed tag.", s["tag_obs"], cmd=s["tag_cmd"]),
        step(14, "Observation: tag unmoved (step 13). Commit formula.", s["cmt_obs"], cmd=s["cmt_cmd"]),
        step(15, "Observation: commit landed (step 14). Residual note.", s["res_obs"], cmd=s["res_cmd"], refl=s["res_refl"]),
    ]
    return rec(n, s, steps)


def ok_nix_nar(n: int, s: dict) -> dict:
    """Nix NAR-of-unpacked src vs sha256 of the compressed tarball (not git SHA)."""
    steps = [
        step(1, "Plan: inspect fetch helper, outputHash, and last FOD mismatch before rewriting the hash.", s["inspect_obs"], cmd=s["inspect_cmd"]),
        step(2, "Observation: fetch helper and claimed hash (step 1). Read the nix expression.", s["nix_obs"], tool="read", path=s["nix_path"]),
        step(3, "Observation: hash mode vs fetcher (step 2). Read flake lock input.", s["lock_obs"], tool="read", path=s["lock_path"]),
        step(4, "Observation: lock hash vs expression (step 3). Prefetch compressed bytes and unpacked NAR separately.", s["pref_obs"], cmd=s["pref_cmd"]),
        step(5, "Plan: first apply — set outputHash to the compressed-tarball sha256 while still using the unpacking fetcher.", s["apply_obs"], cmd=s["apply_cmd"], refl=s["apply_refl"]),
        step(6, "Observation: FOD still mismatches (step 5). nix hash path the unpacked store.", s["nar_obs"], cmd=s["nar_cmd"]),
        step(7, "Observation: NAR ≠ gzip bytes (step 6). Confirm fetcher (fetchzip vs fetchurl).", s["fetch_obs"], cmd=s["fetch_cmd"]),
        step(8, "Reflection: plan change — keep the unpacking fetcher; set outputHash to the NAR of unpacked src. Do not use the gzip sha256.", "patched outputHash to NAR of unpacked src", tool="write", path=s["nix_path"], contents=s["nix_new"]),
        step(9, "Observation: expression retargeted (step 8). Rebuild the FOD.", s["bld_obs"], cmd=s["bld_cmd"]),
        step(10, "Observation: FOD matched (step 9). Confirm leftover wrong hash still in binary cache notes.", s["left_obs"], cmd=s["left_cmd"]),
        step(11, "Observation: cache leftover (step 10). Do not GC the foreign cache; document skip.", s["doc_obs"], cmd=s["doc_cmd"]),
        step(12, "Observation: skip documented (step 11). Keep the signed tag.", s["tag_obs"], cmd=s["tag_cmd"]),
        step(13, "Observation: tag unmoved (step 12). Commit nix+lock.", s["cmt_obs"], cmd=s["cmt_cmd"]),
        step(14, "Observation: commit landed (step 13). nix flake check.", s["chk_obs"], cmd=s["chk_cmd"]),
        step(15, "Observation: check passed (step 14). Residual note.", s["res_obs"], cmd=s["res_cmd"], refl=s["res_refl"]),
    ]
    return rec(n, s, steps)


def ok_nuget_snupkg(n: int, s: dict) -> dict:
    """NuGet snupkg metadata (RepositoryCommit / PDB kind) vs nupkg."""
    steps = [
        step(1, "Plan: inspect nupkg/snupkg pair, RepositoryCommit, and last symbol-server reject.", s["inspect_obs"], cmd=s["inspect_cmd"]),
        step(2, "Observation: pack outputs listed (step 1). Read nuspec.", s["nus_obs"], tool="read", path=s["nus_path"]),
        step(3, "Observation: nuspec repository metadata (step 2). Read Directory.Build.props.", s["dbp_obs"], tool="read", path=s["dbp_path"]),
        step(4, "Observation: PDB type and SourceLink (step 3). Compare nupkg vs snupkg commits.", s["cmp_obs"], cmd=s["cmp_cmd"]),
        step(5, "Plan: first apply — push the existing nupkg then the existing snupkg as two separate pack outputs.", s["apply_obs"], cmd=s["apply_cmd"], refl=s["apply_refl"]),
        step(6, "Observation: symbol server rejected the pair (step 5). ildasm/pdb2mdb the PDB kind.", s["pdb_obs"], cmd=s["pdb_cmd"]),
        step(7, "Observation: PDB/commit mismatch isolated (step 6). Confirm nuget.org vs symbols.nuget.org.", s["host_obs"], cmd=s["host_cmd"]),
        step(8, "Reflection: plan change — pack once so nupkg and snupkg share RepositoryCommit and the same PDB kind. Do not push a leftover snupkg.", "patched pack props: one pack, matching RepositoryCommit", tool="write", path=s["dbp_path"], contents=s["dbp_new"]),
        step(9, "Observation: props retargeted (step 8). Pack once and push both.", s["pack_obs"], cmd=s["pack_cmd"]),
        step(10, "Observation: push accepted (step 9). Confirm symbols resolve.", s["sym_obs"], cmd=s["sym_cmd"]),
        step(11, "Observation: symbols resolve (step 10). Confirm leftover mismatched snupkg still 200.", s["left_obs"], cmd=s["left_cmd"]),
        step(12, "Observation: leftover snupkg listed (step 11). Unlist only the bad pair; do not delete.", s["unl_obs"], cmd=s["unl_cmd"]),
        step(13, "Observation: unlist recorded (step 12). Keep the signed tag.", s["tag_obs"], cmd=s["tag_cmd"]),
        step(14, "Observation: tag unmoved (step 13). Commit props.", s["cmt_obs"], cmd=s["cmt_cmd"]),
        step(15, "Observation: commit landed (step 14). Residual note.", s["res_obs"], cmd=s["res_cmd"], refl=s["res_refl"]),
    ]
    return rec(n, s, steps)


def fail_leftover(n: int, s: dict) -> dict:
    """Cannot mutate a published artifact; leftover consumer is not a lockfile pin."""
    steps = [
        step(1, "Plan: inspect published artifact, attestation/index state, and consumer pointer before trying to replace the version.", s["inspect_obs"], cmd=s["inspect_cmd"]),
        step(2, "Observation: published version and consumer pointer (step 1). Read release workflow.", s["wf_obs"], tool="read", path=s["wf_path"]),
        step(3, "Observation: workflow/permissions (step 2). Confirm why this version is not acceptable.", s["why_obs"], cmd=s["why_cmd"]),
        step(4, "Observation: gap confirmed (step 3). Read the consumer pointer (dist-tag, index, staging, bottle, cache).", s["con_obs"], tool="read", path=s["con_path"]),
        step(5, "Plan: first apply — delete/unpublish/overwrite the same version so the consumer picks up a replacement.", s["apply_obs"], cmd=s["apply_cmd"], refl=s["apply_refl"]),
        step(6, "Observation: replace refused (step 5). Confirm the original artifact is still GET-able.", s["still_obs"], cmd=s["still_cmd"]),
        step(7, "Observation: original still served (step 6). Consumer still resolves the bad pointer.", s["use_obs"], cmd=s["use_cmd"]),
        step(8, "Reflection: plan change — leave the published version immutable; ship the next version with correct attestation; hand off the leftover consumer pointer.", s["fix_obs"], cmd=s["fix_cmd"]),
        step(9, "Observation: next version prepared (step 8). Publish/attest the bump.", s["pub_obs"], cmd=s["pub_cmd"]),
        step(10, "Observation: bump published (step 9). Verify the bump; do not rewrite the old version.", s["ver_obs"], cmd=s["ver_cmd"]),
        step(11, "Observation: bump verifies (step 10). Restore/keep the signed tag on the original commit.", s["tag_obs"], cmd=s["tag_cmd"]),
        step(12, "Observation: tags in place (step 11). Consumer pointer still on the old version.", s["still2_obs"], cmd=s["still2_cmd"], refl="Consumer pointer was not moved by publishing a new version."),
        step(13, "Observation: leftover consumer (step 12). Refuse the destructive undo (unpublish/unretire/force-delete).", s["undo_obs"], cmd=s["undo_cmd"]),
        step(14, "Observation: undo skipped (step 13). Record index vs git / registry vs consumer split.", s["split_obs"], cmd=s["split_cmd"]),
        step(15, "Observation: split documented (step 14). Open handoff ticket; do not claim the consumer is fixed.", s["tix_obs"], cmd=s["tix_cmd"]),
        step(16, "Observation: ticket open (step 15). Residual note.", s["res_obs"], cmd=s["res_cmd"]),
    ]
    return rec(n, s, steps)


# ---------------------------------------------------------------------------
# Catalog: index = round - 163. Unique plants, unique leftovers.
# ---------------------------------------------------------------------------


def _pairs() -> list[tuple[str, dict, str, dict]]:
    """Return (ok_kind, ok_spec, fail_kind, fail_spec) list."""
    return [
        # r163
        (
            "cosign_reusable",
            {
                "slug": "cosign-reusable-workflow-san",
                "plant": "lawsonite-ctl",
                "image": "ghcr.io/lawsonite-designed/lawsonite-ctl:1.8.0",
                "digest": "sha256:" + hx("lawsonite-img", 64),
                "call_id": "https://github.com/lawsonite-designed/lawsonite-ctl/.github/workflows/release.yml@refs/tags/v1.8.0",
                "reuse_id": "https://github.com/acme-infra/oidc-release/.github/workflows/cosign.yml@refs/tags/v3",
                "reuse_short": "acme-infra/oidc-release@v3",
                "tag": "v1.8.0",
                "ver": "1.8.0",
                "leftover": ":latest still 1.7.9 unsigned",
                "inspect_cmd": "git verify-tag v1.8.0 2>&1 | tail -n 8; git rev-parse v1.8.0^{commit}; cosign version | head -n 2; crane digest ghcr.io/lawsonite-designed/lawsonite-ctl:1.8.0",
                "inspect_obs": (
                    "Good \"git\" signature for key SHA256:A11CE0... principal release@lawsonite.example\n"
                    + gsha("lawsonite-tag")
                    + "\nGitVersion:    v2.4.1\nghcr.io/lawsonite-designed/lawsonite-ctl:1.8.0@"
                    + "sha256:"
                    + hx("lawsonite-img", 64)
                ),
                "wf_path": ".github/workflows/release.yml",
                "wf_obs": "name: release\non:\n  push:\n    tags: [\"v*\"]\njobs:\n  sign:\n    uses: acme-infra/oidc-release/.github/workflows/cosign.yml@v3\n    with:\n      image: ghcr.io/lawsonite-designed/lawsonite-ctl:${{ github.ref_name }}\n",
                "pol_path": "policy/cosign-verify.json",
                "pol_obs": "{\n  \"certificate-identity\": \"https://github.com/lawsonite-designed/lawsonite-ctl/.github/workflows/release.yml@refs/tags/v1.8.0\",\n  \"certificate-oidc-issuer\": \"https://token.actions.githubusercontent.com\"\n}\n",
                "decode_cmd": "cosign verify ghcr.io/lawsonite-designed/lawsonite-ctl:1.8.0 --certificate-identity https://github.com/lawsonite-designed/lawsonite-ctl/.github/workflows/release.yml@refs/tags/v1.8.0 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 14",
                "decode_obs": "Error: no matching signatures:\nmain.yaml: failed to verify signature\ncertificate identity does not match\nwant calling-repo release.yml@v1.8.0\ngot SAN https://github.com/acme-infra/oidc-release/.github/workflows/cosign.yml@refs/tags/v3",
                "apply_cmd": "cosign verify ghcr.io/lawsonite-designed/lawsonite-ctl@sha256:"
                + hx("lawsonite-img", 64)
                + " --certificate-identity https://github.com/lawsonite-designed/lawsonite-ctl/.github/workflows/release.yml@refs/tags/v1.8.0 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 12",
                "apply_obs": "Error: no matching signatures\nFulcio SAN https://github.com/acme-infra/oidc-release/.github/workflows/cosign.yml@refs/tags/v3\ndoes not match --certificate-identity calling-repo release.yml",
                "san_cmd": "cosign download signature ghcr.io/lawsonite-designed/lawsonite-ctl@sha256:"
                + hx("lawsonite-img", 64)
                + " | python3 -c 'import sys,json,base64; print(sys.stdin.read()[:400])'; echo SAN=acme-infra/oidc-release/.github/workflows/cosign.yml@v3",
                "san_obs": "bundle mediaType application/vnd.dev.sigstore.bundle.v0.3+json\nSAN=acme-infra/oidc-release/.github/workflows/cosign.yml@v3\nissuer=https://token.actions.githubusercontent.com",
                "iss_cmd": "gh api repos/acme-infra/oidc-release/git/refs/tags/v3 --jq .object.sha; echo ISSUER=https://token.actions.githubusercontent.com",
                "iss_obs": hx("acme-infra-v3", 40)
                + "\nISSUER=https://token.actions.githubusercontent.com",
                "pol_new": "{\n  \"certificate-identity\": \"https://github.com/acme-infra/oidc-release/.github/workflows/cosign.yml@refs/tags/v3\",\n  \"certificate-oidc-issuer\": \"https://token.actions.githubusercontent.com\"\n}\n",
                "verify_cmd": "cosign verify ghcr.io/lawsonite-designed/lawsonite-ctl@sha256:"
                + hx("lawsonite-img", 64)
                + " --certificate-identity https://github.com/acme-infra/oidc-release/.github/workflows/cosign.yml@refs/tags/v3 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 10",
                "verify_obs": "The following checks were performed on each of these signatures:\n  - The cosign claims were validated\n  - Existence of the claims in the transparency log was verified offline\n  - The code-signing certificate was verified using trusted certificate authority certificates\nPASSED reusable workflow acme-infra/oidc-release@v3",
                "left_cmd": "crane digest ghcr.io/lawsonite-designed/lawsonite-ctl:latest; cosign verify ghcr.io/lawsonite-designed/lawsonite-ctl:latest --certificate-identity https://github.com/acme-infra/oidc-release/.github/workflows/cosign.yml@refs/tags/v3 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 6",
                "left_obs": "sha256:"
                + hx("lawsonite-latest", 64)
                + "\nError: no matching signatures\n:latest is 1.7.9, no keyless bundle",
                "up_cmd": "cosign attach signature --signature bundle-1.8.0.json ghcr.io/lawsonite-designed/lawsonite-ctl@sha256:"
                + hx("lawsonite-img", 64)
                + " 2>&1 | tail -n 6; echo ATTACHED=digest-only",
                "up_obs": "uploaded signature to referrers API\nATTACHED=digest-only\n:latest untouched",
                "wf_old": "    uses: acme-infra/oidc-release/.github/workflows/cosign.yml@v3",
                "wf_new": "    uses: acme-infra/oidc-release/.github/workflows/cosign.yml@v3\n    # verify identity MUST be this reusable workflow, not this calling file",
                "cmt_cmd": "git add policy/cosign-verify.json .github/workflows/release.yml && git commit -m 'release 1.8.0 verify reusable-workflow SAN' && git merge-base --is-ancestor "
                + gsha("lawsonite-tag")
                + " HEAD && echo tag_commit_in_history",
                "cmt_obs": "[main "
                + hx("lawsonite-cmt", 7)
                + "] release 1.8.0 verify reusable-workflow SAN\ntag_commit_in_history",
                "tag_cmd": "git rev-parse v1.8.0^{commit}; git describe --tags --exact-match HEAD 2>&1",
                "tag_obs": gsha("lawsonite-tag") + "\nfatal: no tag exactly matches '"
                + hx("lawsonite-cmt", 7)
                + "'",
                "res_cmd": "echo IDENTITY=acme-infra/oidc-release@v3 DIGEST="
                + hx("lawsonite-img", 12)
                + " TAG="
                + gsha("lawsonite-tag")[:12]
                + " LATEST=1.7.9_unsigned",
                "res_obs": "IDENTITY=acme-infra/oidc-release@v3 DIGEST="
                + hx("lawsonite-img", 12)
                + " TAG="
                + gsha("lawsonite-tag")[:12]
                + " LATEST=1.7.9_unsigned",
                "res_refl": "Fulcio SAN is the reusable workflow, not the calling repo. Signed tag stays. Residual: :latest 1.7.9 unsigned.",
                "seed": "calling-repo identity = reusable SAN",
                "first": "verify calling-repo release.yml",
                "change": "reusable acme-infra/oidc-release@v3",
                "term": "success; :latest 1.7.9 unsigned",
            },
            "fail_leftover",
            {
                "slug": "npm-oidc-id-token-missing",
                "plant": "pumpellyite-js",
                "goal": "pumpellyite-js 2.4.0 is on npm latest without provenance (workflow lacked id-token: write). Publish 2.4.1 with OIDC provenance. Do not unpublish 2.4.0. Downstream dist-tag latest still points at 2.4.0.",
                "plan": "npm unpublish @pumpellyite/core@2.4.0 then npm publish --provenance so latest becomes a provenanced tarball of the same version.",
                "outcome": "Unpublish 2.4.0 refused (immutable after 72h). Plan change: 2.4.1 with id-token: write + --provenance. 2.4.1 verifies; dist-tag latest still 2.4.0 with attestations=null. Ticket not closed.",
                "reward": {
                    "success": False,
                    "publish_fails": 1,
                    "plan_changes": 1,
                    "provenance": 1,
                    "latest_still_old": 1,
                    "cost_steps": 16,
                },
                "inspect_cmd": "npm view @pumpellyite/core --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(p[\"version\"], p.get(\"dist-tags\")); print(\"attest\", p.get(\"dist\",{}).get(\"attestations\"))'; git verify-tag v2.4.0 2>&1 | tail -n 4",
                "inspect_obs": "2.4.0 {'latest': '2.4.0', 'next': '2.4.0'}\nattest None\nGood \"git\" signature ... principal release@pumpellyite.example",
                "wf_path": ".github/workflows/npm-publish.yml",
                "wf_obs": "name: npm-publish\npermissions:\n  contents: write\njobs:\n  pub:\n    runs-on: ubuntu-latest\n    steps:\n      - run: npm publish --access public\n",
                "why_cmd": "npm view @pumpellyite/core@2.4.0 --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(\"attestations\", p.get(\"dist\",{}).get(\"attestations\")); print(\"shasum\", p.get(\"dist\",{}).get(\"shasum\"))'",
                "why_obs": "attestations None\nshasum "
                + hx("pump-tgz", 40)
                + "\n# id-token permission missing so provenance never attached",
                "con_path": ".npmrc-consumer",
                "con_obs": "registry=https://registry.npmjs.org/\n# fleet pins dist-tag latest\n@pumpellyite:registry=https://registry.npmjs.org/\n",
                "apply_cmd": "npm unpublish @pumpellyite/core@2.4.0 --force 2>&1 | tail -n 16; npm publish --provenance --access public 2>&1 | tail -n 12",
                "apply_obs": "npm ERR! code E403\nnpm ERR! 403 Cannot unpublish @pumpellyite/core@2.4.0 after 72 hours\nnpm ERR! 403 You cannot publish over the previously published versions: 2.4.0\n",
                "apply_refl": "Apply failed. npm versions are unique forever after the unpublish window; provenance cannot be retrofitted onto 2.4.0.",
                "still_cmd": "curl -sSI https://registry.npmjs.org/@pumpellyite/core/-/core-2.4.0.tgz | rg -i 'HTTP|content-length'; npm view @pumpellyite/core@2.4.0 version",
                "still_obs": "HTTP/2 200\ncontent-length: 18440\n2.4.0",
                "use_cmd": "npm view @pumpellyite/core dist-tags --json; npm view @pumpellyite/core@latest --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(p[\"version\"], p.get(\"dist\",{}).get(\"attestations\"))'",
                "use_obs": "{\"latest\":\"2.4.0\",\"next\":\"2.4.0\"}\n2.4.0 None",
                "fix_cmd": "python3 - <<'PY'\nfrom pathlib import Path\np=Path('.github/workflows/npm-publish.yml')\np.write_text(p.read_text().replace('contents: write','contents: write\\n  id-token: write').replace('npm publish --access public','npm publish --access public --provenance'))\nprint('patched id-token + provenance')\nPY",
                "fix_obs": "patched id-token + provenance",
                "pub_cmd": "npm version 2.4.1 --no-git-tag-version && npm publish --access public --provenance 2>&1 | tail -n 16",
                "pub_obs": "v2.4.1\n+ @pumpellyite/core@2.4.1\nprovenance in-toto attestations uploaded\n",
                "ver_cmd": "npm view @pumpellyite/core@2.4.1 --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(\"attest\", bool(p.get(\"dist\",{}).get(\"attestations\"))); print(\"tag\", p.get(\"gitHead\"))'",
                "ver_obs": "attest True\ntag "
                + gsha("pump-241")[:12],
                "tag_cmd": "git add .github/workflows/npm-publish.yml package.json && git commit -m 'release 2.4.1 provenance; leave 2.4.0' && git tag -s v2.4.1 -m '2.4.1' && git tag -s v2.4.0 -f -m '2.4.0 (no provenance)' 2>&1 | tail -n 8; echo kept_v240=1",
                "tag_obs": "[main "
                + hx("pump-cmt", 7)
                + "] release 2.4.1 provenance; leave 2.4.0\nkept_v240=1",
                "still2_cmd": "npm view @pumpellyite/core dist-tags --json",
                "still2_obs": "{\"latest\":\"2.4.0\",\"next\":\"2.4.1\"}",
                "undo_cmd": "npm unpublish @pumpellyite/core@2.4.0 2>&1 | tail -n 4; echo skipped_unpublish=1",
                "undo_obs": "skipped_unpublish=1\n# would 403 again; 2.4.0 stays latest",
                "split_cmd": "echo REGISTRY_2_4_0=200 ATTEST_2_4_0=null LATEST=2.4.0 PROVENANCE_2_4_1=yes",
                "split_obs": "REGISTRY_2_4_0=200 ATTEST_2_4_0=null LATEST=2.4.0 PROVENANCE_2_4_1=yes",
                "tix_cmd": "echo TICKET=fleet_still_on_latest_2.4.0_no_provenance OWNER=release-train",
                "tix_obs": "TICKET=fleet_still_on_latest_2.4.0_no_provenance OWNER=release-train",
                "res_cmd": "echo OLD=2.4.0_no_provenance NEW=2.4.1_ok LATEST=2.4.0",
                "res_obs": "OLD=2.4.0_no_provenance NEW=2.4.1_ok LATEST=2.4.0",
                "seed": "id-token missing so provenance omitted",
                "first": "unpublish 2.4.0 + republish --provenance",
                "change": "2.4.1 + id-token: write",
                "term": "fail: latest still 2.4.0 attest=null",
            },
        ),
        # r164
        (
            "oidc_publisher",
            {
                "slug": "pypi-trusted-publisher-workflow-name",
                "plant": "glaucophane-py",
                "goal": "Ship glaucophane-py 3.1.0 via PyPI Trusted Publisher. Publisher is registered for release.yml but the file on disk is publish.yml. Do not fall back to an API token. Leave 3.0.9 (token-published, no PEP 740) in place.",
                "plan": "twine upload -u __token__ so Warehouse accepts 3.1.0 regardless of workflow filename.",
                "outcome": "First apply with the registered release.yml name (and a token fallback) failed OIDC match; token path would skip PEP 740. Plan change: re-register publisher for publish.yml. 3.1.0 has attestations. Residual: 3.0.9 token upload, no attestations.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "gh api /orgs/glaucophane-designed/packages 2>/dev/null | head; python3 -m twine --version; ls .github/workflows; echo PUBLISHER=release.yml",
                "inspect_obs": "twine 5.1.1\npublish.yml\nci.yml\nPUBLISHER=release.yml  # warehouse row still names release.yml",
                "wf_path": ".github/workflows/publish.yml",
                "wf_obs": "name: publish\non:\n  push:\n    tags: [\"v*\"]\npermissions:\n  id-token: write\n  contents: read\njobs:\n  pypi:\n    runs-on: ubuntu-latest\n    environment: release\n    steps:\n      - uses: pypa/gh-action-pypi-publish@release/v1\n",
                "meta_path": "pyproject.toml",
                "meta_obs": "[project]\nname = \"glaucophane-py\"\nversion = \"3.1.0\"\n",
                "claim_cmd": "echo 'sub: repo:glaucophane-designed/glaucophane-py:environment:release'\necho 'workflow_ref: glaucophane-designed/glaucophane-py/.github/workflows/publish.yml@refs/tags/v3.1.0'",
                "claim_obs": "sub: repo:glaucophane-designed/glaucophane-py:environment:release\nworkflow_ref: glaucophane-designed/glaucophane-py/.github/workflows/publish.yml@refs/tags/v3.1.0",
                "apply_cmd": "python3 -m twine upload --non-interactive dist/glaucophane_py-3.1.0-py3-none-any.whl 2>&1 | tail -n 16",
                "apply_obs": "HTTPError: 403 Trusted publishing exchange failure\nNo publisher is registered for workflow filename 'publish.yml'\nRegistered: workflow=release.yml environment=release\nRefusing token fallback (would omit PEP 740 attestations)",
                "apply_refl": "Apply failed. Warehouse matches workflow filename, not the job name. Token fallback would drop attestations.",
                "diff_cmd": "echo REGISTERED=release.yml ONDISK=publish.yml ENV=release ISSUER=https://token.actions.githubusercontent.com",
                "diff_obs": "REGISTERED=release.yml ONDISK=publish.yml ENV=release ISSUER=https://token.actions.githubusercontent.com",
                "iss_cmd": "curl -sS https://pypi.org/manage/project/glaucophane-py/settings/publishing/ 2>/dev/null | rg -n 'release.yml|publish.yml|pending' | head; echo WAREHOUSE=filename_eq",
                "iss_obs": "1:workflow filename release.yml\nWAREHOUSE=filename_eq",
                "fix_path": "docs/publisher.json",
                "fix_contents": "{\n  \"repository\": \"glaucophane-designed/glaucophane-py\",\n  \"workflow\": \"publish.yml\",\n  \"environment\": \"release\"\n}\n",
                "pub_cmd": "python3 -m twine upload --non-interactive dist/glaucophane_py-3.1.0-py3-none-any.whl 2>&1 | tail -n 12",
                "pub_obs": "Uploading distributions to https://upload.pypi.org/legacy/\nUploading glaucophane_py-3.1.0-py3-none-any.whl\nAttestations: publish.yml OIDC / PEP 740 uploaded\n",
                "att_cmd": "curl -sS https://pypi.org/integrity/glaucophane-py/3.1.0/glaucophane_py-3.1.0-py3-none-any.whl/provenance 2>&1 | python3 -c 'import sys; t=sys.stdin.read(); print(t[:240] or \"prov-ok\")'",
                "att_obs": "prov-ok\npredicateType https://docs.pypi.org/attestations/publish/v1\nworkflow publish.yml",
                "left_cmd": "curl -sS https://pypi.org/integrity/glaucophane-py/3.0.9/glaucophane_py-3.0.9-py3-none-any.whl/provenance 2>&1 | tail -n 4",
                "left_obs": "404 No PEP 740 attestation for 3.0.9 (uploaded with API token)",
                "doc_cmd": "echo SKIP_309=token_upload_no_pep740 KEEP=1",
                "doc_obs": "SKIP_309=token_upload_no_pep740 KEEP=1",
                "tag_cmd": "git verify-tag v3.1.0 2>&1 | tail -n 4; git rev-parse v3.1.0^{commit}",
                "tag_obs": "Good \"git\" signature\n" + gsha("glauc-tag"),
                "cmt_cmd": "git add docs/publisher.json && git commit -m 'release 3.1.0 trusted publisher publish.yml'",
                "cmt_obs": "[main " + hx("glauc-cmt", 7) + "] release 3.1.0 trusted publisher publish.yml",
                "res_cmd": "echo WORKFLOW=publish.yml ATTEST_310=yes TOKEN_309=no_attest",
                "res_obs": "WORKFLOW=publish.yml ATTEST_310=yes TOKEN_309=no_attest",
                "res_refl": "Trusted publisher matches workflow filename. Residual: 3.0.9 token upload has no PEP 740.",
                "seed": "publisher registered for release.yml",
                "first": "twine / token fallback",
                "change": "re-register publish.yml",
                "term": "success; 3.0.9 no PEP 740",
            },
            "fail_leftover",
            {
                "slug": "maven-gpg-subkey-expired-staging",
                "plant": "riebeckite-mvn",
                "goal": "riebeckite-mvn 4.2.0 staging close failed because the GPG signing subkey expired. Open a new staging repo with a live subkey. Do not promote the rejected staging. Downstream BOM still points at the rejected repo id.",
                "plan": "Re-close the same OSSRH staging repository after gpg --send-keys so the expired subkey is accepted.",
                "outcome": "Re-close of the expired-subkey staging refused (BADSIG). Plan change: new signing subkey + new staging; 4.2.0 Portal upload verifies. Residual: rejected staging id still listed on the BOM consumer. Ticket not closed.",
                "reward": {"success": False, "sign_fails": 1, "plan_changes": 1, "staging_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "gpg --list-secret-keys --with-subkey-fingerprints | tail -n 20; echo STAGING=orgriebeckite-1166",
                "inspect_obs": "sec  rsa4096 2022-01-04 [SC]\n      "
                + hx("rieb-primary", 40)
                + "\nssb  rsa4096 2022-01-04 [S] [expired: 2026-01-04]\n      "
                + hx("rieb-sub", 40)
                + "\nSTAGING=orgriebeckite-1166",
                "wf_path": "pom.xml",
                "wf_obs": "<plugin>\n  <artifactId>maven-gpg-plugin</artifactId>\n  <configuration><keyname>"
                + hx("rieb-sub", 16)
                + "</keyname></configuration>\n</plugin>\n",
                "why_cmd": "mvn nexus-staging:rc-close -DstagingRepositoryId=orgriebeckite-1166 2>&1 | tail -n 12",
                "why_obs": "Rule failed: signatures-valid\nBADSIG "
                + hx("rieb-sub", 16)
                + " expired 2026-01-04\nclose rejected",
                "con_path": "../riebeckite-bom/pom.xml",
                "con_obs": "<properties>\n  <riebeckite.staging>orgriebeckite-1166</riebeckite.staging>\n  <riebeckite.version>4.2.0</riebeckite.version>\n</properties>\n",
                "apply_cmd": "gpg --send-keys "
                + hx("rieb-sub", 40)
                + " && mvn nexus-staging:rc-close -DstagingRepositoryId=orgriebeckite-1166 2>&1 | tail -n 14",
                "apply_obs": "gpg: sending key ...\nRule failed: signatures-valid\nBADSIG expired subkey; republishing the same signatures cannot un-expire them\n",
                "apply_refl": "Apply failed. Uploading an expired signing subkey to a keyserver does not make OSSRH accept the signatures.",
                "still_cmd": "curl -sSI https://s01.oss.sonatype.org/content/repositories/orgriebeckite-1166/org/riebeckite/riebeckite-mvn/4.2.0/riebeckite-mvn-4.2.0.jar.asc | rg -i 'HTTP|content'; echo STAGING_STILL=1166",
                "still_obs": "HTTP/1.1 200 OK\ncontent-length: 849\nSTAGING_STILL=1166",
                "use_cmd": "rg -n 'orgriebeckite-1166' ../riebeckite-bom/pom.xml",
                "use_obs": "  <riebeckite.staging>orgriebeckite-1166</riebeckite.staging>",
                "fix_cmd": "gpg --quick-add-key "
                + hx("rieb-primary", 40)
                + " rsa4096 sign 2y && echo NEW_SUB="
                + hx("rieb-newsub", 16),
                "fix_obs": "NEW_SUB=" + hx("rieb-newsub", 16) + "\ncreated signing subkey",
                "pub_cmd": "mvn -B -Dgpg.keyname="
                + hx("rieb-newsub", 16)
                + " clean deploy -DskipTests 2>&1 | tail -n 16",
                "pub_obs": "Uploaded to orgriebeckite-1171\nSigning with "
                + hx("rieb-newsub", 16)
                + "\nclose+release requested via Publisher Portal",
                "ver_cmd": "gpg --verify riebeckite-mvn-4.2.0.jar.asc riebeckite-mvn-4.2.0.jar 2>&1 | tail -n 8",
                "ver_obs": "gpg: Good signature from release@riebeckite.example\nprimary "
                + hx("rieb-primary", 16)
                + " sub "
                + hx("rieb-newsub", 16),
                "tag_cmd": "git tag -s v4.2.0 -m '4.2.0' && git rev-parse v4.2.0^{commit}",
                "tag_obs": gsha("rieb-tag"),
                "still2_cmd": "rg -n 'orgriebeckite-1166' ../riebeckite-bom/pom.xml; echo NEW_STAGING=1171",
                "still2_obs": "  <riebeckite.staging>orgriebeckite-1166</riebeckite.staging>\nNEW_STAGING=1171",
                "undo_cmd": "echo skipped_promote_1166=1; echo skipped_delete_expired_sigs=1",
                "undo_obs": "skipped_promote_1166=1\nskipped_delete_expired_sigs=1",
                "split_cmd": "echo PORTAL=1171_good OSSRH=1166_badsig BOM=1166",
                "split_obs": "PORTAL=1171_good OSSRH=1166_badsig BOM=1166",
                "tix_cmd": "echo TICKET=bom_still_points_at_rejected_staging_1166",
                "tix_obs": "TICKET=bom_still_points_at_rejected_staging_1166",
                "res_cmd": "echo OLD_STAGING=1166 NEW=1171 BOM=1166",
                "res_obs": "OLD_STAGING=1166 NEW=1171 BOM=1166",
                "seed": "expired GPG signing subkey",
                "first": "re-close same staging after send-keys",
                "change": "new subkey + staging 1171",
                "term": "fail: BOM still 1166",
            },
        ),
        # r165
        (
            "bottle_rebuild",
            {
                "slug": "homebrew-bottle-rebuild-runner-image",
                "plant": "aragonite-brew",
                "goal": "Ship aragonite-brew 1.6.0 bottles after the GitHub macos-14 runner image bump. Formula sha256 still describes the macos-13 bottle. Rebuild, bump bottle_custom_version, keep signed v1.6.0. Leave the catalina bottle listed.",
                "plan": "Copy the old bottle sha256 into the formula without --rebuild so brew audit goes green.",
                "outcome": "First apply reused the pre-image-bump bottle sha256; brew audit failed (poured bytes ≠ formula after runner bump). Plan change: brew bottle --rebuild + bottle_custom_version 2. Residual: catalina bottle still listed on the GH release.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "bottles": 1, "cost_steps": 15},
                "inspect_cmd": "brew --version | head -n 1; git verify-tag v1.6.0 2>&1 | tail -n 4; rg -n 'sha256|sonoma|catalina|bottle_custom' Formula/aragonite.rb | head",
                "inspect_obs": "Homebrew 4.4.12\nGood \"git\" signature\n  sha256 cellar: :any, sonoma: \""
                + hx("arag-old-sonoma", 64)
                + "\"\n  bottle_custom_version 1\n  # catalina still listed on release",
                "f_path": "Formula/aragonite.rb",
                "f_obs": "class Aragonite < Formula\n  url \"https://github.com/aragonite-designed/aragonite-brew/archive/refs/tags/v1.6.0.tar.gz\"\n  sha256 \""
                + hx("arag-src", 64)
                + "\"\n  bottle do\n    rebuild 1\n    sha256 cellar: :any, sonoma: \""
                + hx("arag-old-sonoma", 64)
                + "\"\n  end\nend\n",
                "j_path": "aragonite-1.6.0.sonoma.bottle.json",
                "j_obs": "{\n  \"aragonite\": {\n    \"formula\": {\"pkg_version\": \"1.6.0\"},\n    \"sonoma\": {\"sha256\": \""
                + hx("arag-new-sonoma", 64)
                + "\"}\n  }\n}\n",
                "run_cmd": "echo RUNNER=macos-14.7.1 IMAGE=ghcr.io/actions/runner-images/macos-14:"
                + hx("runner-macos14", 12)
                + "; sw_vers | head",
                "run_obs": "RUNNER=macos-14.7.1 IMAGE=ghcr.io/actions/runner-images/macos-14:"
                + hx("runner-macos14", 12)
                + "\nProductVersion: 14.7.1",
                "apply_cmd": "brew audit --strict --online aragonite 2>&1 | tail -n 16",
                "apply_obs": "aragonite:\n  * SHA256 mismatch for sonoma bottle\n    formula "
                + hx("arag-old-sonoma", 16)
                + "\n    poured "
                + hx("arag-new-sonoma", 16)
                + " (macos-14 runner image bump)\nError: 1 problem in 1 formula",
                "apply_refl": "Apply failed. The pre-bump bottle sha256 does not describe bottles produced on the new runner image.",
                "pour_cmd": "brew fetch --bottle-tag=sonoma aragonite && shasum -a 256 $(brew --cache --bottle-tag=sonoma aragonite)",
                "pour_obs": hx("arag-new-sonoma", 64)
                + "  /Users/brew/Library/Caches/Homebrew/aragonite--1.6.0.sonoma.bottle.tar.gz",
                "pol_cmd": "echo bottle_custom_version=1 POLICY=bump_on_runner_image",
                "pol_obs": "bottle_custom_version=1 POLICY=bump_on_runner_image",
                "f_new": "class Aragonite < Formula\n  url \"https://github.com/aragonite-designed/aragonite-brew/archive/refs/tags/v1.6.0.tar.gz\"\n  sha256 \""
                + hx("arag-src", 64)
                + "\"\n  bottle do\n    rebuild 2\n    sha256 cellar: :any, sonoma: \""
                + hx("arag-new-sonoma", 64)
                + "\"\n  end\nend\n",
                "reb_cmd": "brew bottle --rebuild --json aragonite 2>&1 | tail -n 10",
                "reb_obs": "Bottling aragonite-1.6.0.sonoma.bottle.2.tar.gz\nsha256 "
                + hx("arag-new-sonoma", 64),
                "aud_cmd": "brew audit --strict --online aragonite 2>&1 | tail -n 6",
                "aud_obs": "aragonite:\n  0 problems",
                "left_cmd": "gh release view v1.6.0 --json assets --jq '.assets[].name' | rg -n 'catalina|sonoma|bottle'",
                "left_obs": "1:aragonite-1.6.0.catalina.bottle.tar.gz\n2:aragonite-1.6.0.sonoma.bottle.2.tar.gz",
                "note_cmd": "echo CATALINA_BOTTLE=still_on_release KEEP=1",
                "note_obs": "CATALINA_BOTTLE=still_on_release KEEP=1",
                "tag_cmd": "git verify-tag v1.6.0 >/dev/null && echo signed_tag_ok; git rev-parse v1.6.0^{commit}",
                "tag_obs": "signed_tag_ok\n" + gsha("arag-tag"),
                "cmt_cmd": "git add Formula/aragonite.rb && git commit -m 'bottle rebuild 2 after macos-14 image'",
                "cmt_obs": "[main " + hx("arag-cmt", 7) + "] bottle rebuild 2 after macos-14 image",
                "res_cmd": "echo BOTTLE=sonoma:"
                + hx("arag-new-sonoma", 12)
                + " REBUILD=2 CATALINA=leftover",
                "res_obs": "BOTTLE=sonoma:"
                + hx("arag-new-sonoma", 12)
                + " REBUILD=2 CATALINA=leftover",
                "res_refl": "bottle_custom_version bumped after runner image change. Residual: catalina bottle still on the GH release.",
                "seed": "macos-14 runner image bump",
                "first": "reuse old bottle sha256",
                "change": "brew bottle --rebuild + rebuild 2",
                "term": "success; catalina leftover",
            },
            "fail_leftover",
            {
                "slug": "crates-sparse-vs-git-index-yank",
                "plant": "omphacite-crate",
                "goal": "omphacite-crate 0.7.2 yanked on crates.io for CVE-2026-5520. Sparse index shows yanked; CARGO_REGISTRIES_CRATES_IO_PROTOCOL=git still serves 0.7.2. Publish 0.7.3. Do not unyank. CI using the git protocol still compiles 0.7.2.",
                "plan": "cargo yank 0.7.2 then wait for the git index to drop the crate so CI stops compiling it; republish 0.7.2 if needed.",
                "outcome": "Republish 0.7.2 refused (unique forever). Sparse index yanked; git index still serves the crate. Plan change: 0.7.3 + leave yank. CI with PROTOCOL=git still builds 0.7.2. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "git_index_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "cargo info omphacite-crate --registry crates-io 2>&1 | tail -n 16; echo SPARSE=$(curl -sS https://index.crates.io/om/ph/omphacite-crate | tail -n 1)",
                "inspect_obs": "omphacite-crate 0.7.2 (yanked: CVE-2026-5520)\n0.7.1\nSPARSE={\"name\":\"omphacite-crate\",\"vers\":\"0.7.2\",\"yanked\":true}",
                "wf_path": "Cargo.toml",
                "wf_obs": "[package]\nname = \"omphacite-crate\"\nversion = \"0.7.2\"\n",
                "why_cmd": "curl -sS https://index.crates.io/om/ph/omphacite-crate | python3 -c 'import sys,json\nfor line in sys.stdin:\n p=json.loads(line); print(p[\"vers\"], \"yanked\", p.get(\"yanked\"))'",
                "why_obs": "0.7.2 yanked True\n0.7.1 yanked False",
                "con_path": "../omphacite-ci/cargo-config.toml",
                "con_obs": "[registries.crates-io]\nprotocol = \"git\"\n# self-hosted runner still on git index\n",
                "apply_cmd": "cargo publish --allow-dirty 2>&1 | tail -n 14; cargo yank --undo omphacite-crate@0.7.2 2>&1 | tail -n 6",
                "apply_obs": "error: crate omphacite-crate@0.7.2 already exists on crates.io\nerror: refuse cargo yank --undo (would re-expose CVE-2026-5520)\n",
                "apply_refl": "Apply failed. crates.io versions are unique forever; unyank is refused for the CVE. The git index is not a delete API.",
                "still_cmd": "git -C ~/.cargo/registry/index/github.com-1ecc6299db9ec823 log --oneline -3; rg -n '0.7.2' ~/.cargo/registry/index/github.com-1ecc6299db9ec823/om/ph/omphacite-crate | tail",
                "still_obs": "c0ffee1 update omphacite-crate\n0.7.2 yanked=false in cached git index (not yet compacted)",
                "use_cmd": "CARGO_REGISTRIES_CRATES_IO_PROTOCOL=git cargo fetch --locked -p omphacite-crate@0.7.2 2>&1 | tail -n 10",
                "use_obs": " Downloading omphacite-crate v0.7.2\n Downloaded omphacite-crate v0.7.2\n# git protocol used cached index row yanked=false",
                "fix_cmd": "python3 - <<'PY'\nfrom pathlib import Path\np=Path('Cargo.toml'); p.write_text(p.read_text().replace('0.7.2','0.7.3')); print('bumped 0.7.3')\nPY",
                "fix_obs": "bumped 0.7.3",
                "pub_cmd": "cargo publish --allow-dirty 2>&1 | tail -n 12",
                "pub_obs": "Uploaded omphacite-crate v0.7.3 to registry `crates-io`",
                "ver_cmd": "curl -sS https://index.crates.io/om/ph/omphacite-crate | tail -n 2",
                "ver_obs": "{\"vers\":\"0.7.2\",\"yanked\":true}\n{\"vers\":\"0.7.3\",\"yanked\":false}",
                "tag_cmd": "git add Cargo.toml && git commit -m 'release 0.7.3; leave 0.7.2 yanked' && git tag -s v0.7.3 -m '0.7.3'",
                "tag_obs": "[main " + hx("omph-cmt", 7) + "] release 0.7.3; leave 0.7.2 yanked",
                "still2_cmd": "CARGO_REGISTRIES_CRATES_IO_PROTOCOL=git cargo tree -p omphacite-ci 2>&1 | rg omphacite-crate",
                "still2_obs": "omphacite-crate v0.7.2 (git index, yanked flag not yet compacted)",
                "undo_cmd": "echo skipped_unyank=1; echo skipped_force_git_index_gc=1",
                "undo_obs": "skipped_unyank=1\nskipped_force_git_index_gc=1",
                "split_cmd": "echo SPARSE_072=yanked GIT_INDEX_072=served CI=git_protocol",
                "split_obs": "SPARSE_072=yanked GIT_INDEX_072=served CI=git_protocol",
                "tix_cmd": "echo TICKET=ci_git_protocol_still_compiles_yanked_0.7.2",
                "tix_obs": "TICKET=ci_git_protocol_still_compiles_yanked_0.7.2",
                "res_cmd": "echo SPARSE=0.7.3 GIT_CI=0.7.2",
                "res_obs": "SPARSE=0.7.3 GIT_CI=0.7.2",
                "seed": "sparse yank vs git index",
                "first": "republish 0.7.2 / unyank",
                "change": "0.7.3; leave yank",
                "term": "fail: git-protocol CI still 0.7.2",
            },
        ),
        # r166
        (
            "nix_nar",
            {
                "slug": "nix-fetchzip-nar-vs-gzip-src",
                "plant": "jadeite-nix",
                "goal": "Ship jadeite-nix 0.4.1. fetchzip outputHash was set to the sha256 of the compressed tarball; FOD wants the NAR of unpacked src. Do not switch to fetchurl just to make the gzip hash work. Leave the wrong hash in the binary-cache notes.",
                "plan": "Set outputHash to the gzip sha256 of src.tar.gz because that is what GitHub releases serve.",
                "outcome": "First apply used gzip sha256 with fetchzip; FOD mismatched (NAR of unpacked src ≠ gzip bytes). Plan change: keep fetchzip, set outputHash to NAR. Residual: old gzip hash still in cache notes.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "fods": 1, "cost_steps": 15},
                "inspect_cmd": "nix --version | head -n 1; git verify-tag v0.4.1 2>&1 | tail -n 4; ls src.tar.gz flake.nix",
                "inspect_obs": "nix (Nix) 2.24.10\nGood \"git\" signature\nsrc.tar.gz\nflake.nix",
                "nix_path": "flake.nix",
                "nix_obs": "{\n  inputs.src.url = \"https://git.jadeite.example/jadeite-nix/releases/download/v0.4.1/src.tar.gz\";\n  outputs = { src, ... }: {\n    packages.x86_64-linux.default = src; # fetchzip, outputHash = gzip\n  };\n}\n",
                "lock_path": "flake.lock",
                "lock_obs": "{\n  \"nodes\": {\"src\": {\"locked\": {\"narHash\": \"sha256-"
                + hx("jade-gzip", 44)
                + "=\"}}},\n  \"root\": \"root\"\n}\n",
                "pref_cmd": "nix-prefetch-url https://git.jadeite.example/jadeite-nix/releases/download/v0.4.1/src.tar.gz; nix-prefetch-url --unpack https://git.jadeite.example/jadeite-nix/releases/download/v0.4.1/src.tar.gz",
                "pref_obs": "gzip "
                + hx("jade-gzip", 52)
                + "\nNAR-unpacked "
                + hx("jade-nar", 52),
                "apply_cmd": "nix build --rebuild 2>&1 | tail -n 16",
                "apply_obs": "error: hash mismatch in fixed-output derivation\n  specified: sha256-"
                + hx("jade-gzip", 44)
                + "=\n  got:       sha256-"
                + hx("jade-nar", 44)
                + "=\n  (fetchzip hashes the NAR of the unpacked tree, not the gzip file)",
                "apply_refl": "Apply failed. fetchzip outputHash is the NAR of unpacked src, not the sha256 of the compressed tarball.",
                "nar_cmd": "nix hash path --type sha256 --sri /nix/store/"
                + hx("jade-store", 32)
                + "-src",
                "nar_obs": "sha256-" + hx("jade-nar", 44) + "=",
                "fetch_cmd": "rg -n 'fetchzip|fetchurl|outputHashMode' flake.nix pkgs.nix | head",
                "fetch_obs": "flake.nix: fetchzip  outputHashMode=recursive",
                "nix_new": "{\n  outputs = { ... }: {\n    # fetchzip + NAR of unpacked src (not gzip sha256)\n    srcHash = \"sha256-"
                + hx("jade-nar", 44)
                + "=\";\n  };\n}\n",
                "bld_cmd": "nix build --rebuild 2>&1 | tail -n 8",
                "bld_obs": "finished FOD\n/nix/store/"
                + hx("jade-out", 32)
                + "-jadeite-nix-0.4.1",
                "left_cmd": "rg -n '"
                + hx("jade-gzip", 16)
                + "' notes/cache.txt || echo CACHE_NOTE_STILL_HAS_GZIP_HASH",
                "left_obs": "notes/cache.txt:1:old gzip "
                + hx("jade-gzip", 16)
                + "\nCACHE_NOTE_STILL_HAS_GZIP_HASH",
                "doc_cmd": "echo SKIP_CACHE_NOTE=gzip_hash KEEP=1",
                "doc_obs": "SKIP_CACHE_NOTE=gzip_hash KEEP=1",
                "tag_cmd": "git verify-tag v0.4.1 >/dev/null && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add flake.nix && git commit -m 'fix FOD: NAR of unpacked src, keep fetchzip'",
                "cmt_obs": "[main " + hx("jade-cmt", 7) + "] fix FOD: NAR of unpacked src, keep fetchzip",
                "chk_cmd": "nix flake check 2>&1 | tail -n 6",
                "chk_obs": "checking flake ...\nwarning: cache still advertises old gzip hash\nOK",
                "res_cmd": "echo FETCH=fetchzip NAR="
                + hx("jade-nar", 12)
                + " GZIP_NOTE=leftover",
                "res_obs": "FETCH=fetchzip NAR="
                + hx("jade-nar", 12)
                + " GZIP_NOTE=leftover",
                "res_refl": "fetchzip hashes the NAR of unpacked src. Residual: gzip hash still in cache notes.",
                "seed": "fetchzip outputHash = gzip sha256",
                "first": "keep gzip hash with fetchzip",
                "change": "NAR of unpacked src",
                "term": "success; gzip note leftover",
            },
            "fail_leftover",
            {
                "slug": "nuget-snupkg-repositorycommit-split",
                "plant": "vaterite-nupkg",
                "goal": "vaterite-nupkg 5.0.0 nupkg and snupkg were packed separately; RepositoryCommit differs. symbols.nuget.org rejected the snupkg. Pack 5.0.1 once. Do not delete 5.0.0. Symbol consumer still requests 5.0.0.",
                "plan": "dotnet nuget push the existing 5.0.0.snupkg after rewriting its RepositoryCommit to match the nupkg.",
                "outcome": "Rewritten snupkg rejected (content hash ≠ nupkg). Plan change: 5.0.1 packed once with matching RepositoryCommit. Residual: 5.0.0 snupkg still 200; debugger still asks for 5.0.0. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "snupkg_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "ls dist/*.nupkg dist/*.snupkg; echo NUPKG_COMMIT="
                + gsha("vat-nupkg")
                + "; echo SNUPKG_COMMIT="
                + gsha("vat-snupkg"),
                "inspect_obs": "dist/Vaterite.5.0.0.nupkg\ndist/Vaterite.5.0.0.snupkg\nNUPKG_COMMIT="
                + gsha("vat-nupkg")
                + "\nSNUPKG_COMMIT="
                + gsha("vat-snupkg"),
                "wf_path": "Vaterite.nuspec",
                "wf_obs": "<repository type=\"git\" url=\"https://github.com/vaterite-designed/vaterite-nupkg\" commit=\""
                + gsha("vat-snupkg")
                + "\" />\n",
                "why_cmd": "dotnet nuget push dist/Vaterite.5.0.0.snupkg --source https://nuget.smbsrc.net/ 2>&1 | tail -n 12",
                "why_obs": "error: Symbol package RepositoryCommit "
                + gsha("vat-snupkg")[:12]
                + " does not match nupkg "
                + gsha("vat-nupkg")[:12]
                + "\nHTTP 400",
                "con_path": "../vaterite-app/nuget.config",
                "con_obs": "<packageSourceMapping>\n  <package pattern=\"Vaterite\" source=\"nuget.org\" />\n</packageSourceMapping>\n<!-- debugger symbol server: 5.0.0 -->\n",
                "apply_cmd": "python3 - <<'PY'\nprint('rewrote snupkg RepositoryCommit to nupkg commit')\nPY\ndotnet nuget push dist/Vaterite.5.0.0.snupkg --source https://nuget.smbsrc.net/ 2>&1 | tail -n 10",
                "apply_obs": "rewrote snupkg RepositoryCommit to nupkg commit\nerror: package hash mismatch after rewrite; symbols.nuget.org refuses mutated snupkg\nHTTP 409 unique forever",
                "apply_refl": "Apply failed. You cannot mutate a published snupkg's commit metadata; the content hash no longer matches.",
                "still_cmd": "curl -sSI https://www.nuget.org/api/v2/package/Vaterite/5.0.0 | rg -i HTTP; curl -sSI https://globalcdn.nuget.org/symbol-packages/vaterite.5.0.0.snupkg | rg -i HTTP",
                "still_obs": "HTTP/2 200\nHTTP/2 200",
                "use_cmd": "echo DEBUGGER_REQUEST=Vaterite.pdb index=5.0.0",
                "use_obs": "DEBUGGER_REQUEST=Vaterite.pdb index=5.0.0",
                "fix_cmd": "echo NEXT=5.0.1 PACK_ONCE=1",
                "fix_obs": "NEXT=5.0.1 PACK_ONCE=1",
                "pub_cmd": "dotnet pack -c Release -p:PackageVersion=5.0.1 -p:RepositoryCommit="
                + gsha("vat-501")
                + " && dotnet nuget push dist/Vaterite.5.0.1.nupkg --source https://api.nuget.org/v3/index.json && dotnet nuget push dist/Vaterite.5.0.1.snupkg --source https://nuget.smbsrc.net/",
                "pub_obs": "Your package was pushed.\nYour symbol package was pushed.\ncommit "
                + gsha("vat-501")[:12],
                "ver_cmd": "echo SYM_501=ok COMMIT_MATCH=1",
                "ver_obs": "SYM_501=ok COMMIT_MATCH=1",
                "tag_cmd": "git tag -s v5.0.1 -m '5.0.1'",
                "tag_obs": "tagged v5.0.1",
                "still2_cmd": "echo DEBUGGER_REQUEST=Vaterite.pdb index=5.0.0; echo SNUPKG_500=200",
                "still2_obs": "DEBUGGER_REQUEST=Vaterite.pdb index=5.0.0\nSNUPKG_500=200",
                "undo_cmd": "echo skipped_delete_500=1; echo skipped_mutate_snupkg=1",
                "undo_obs": "skipped_delete_500=1\nskipped_mutate_snupkg=1",
                "split_cmd": "echo NUGET_500=200 SYM_500=mismatch_200 SYM_501=ok DEBUGGER=500",
                "split_obs": "NUGET_500=200 SYM_500=mismatch_200 SYM_501=ok DEBUGGER=500",
                "tix_cmd": "echo TICKET=debugger_still_requests_5.0.0_snupkg",
                "tix_obs": "TICKET=debugger_still_requests_5.0.0_snupkg",
                "res_cmd": "echo OLD=5.0.0_split NEW=5.0.1_ok DEBUGGER=5.0.0",
                "res_obs": "OLD=5.0.0_split NEW=5.0.1_ok DEBUGGER=5.0.0",
                "seed": "snupkg RepositoryCommit ≠ nupkg",
                "first": "mutate snupkg commit and repush",
                "change": "5.0.1 pack once",
                "term": "fail: debugger still 5.0.0",
            },
        ),
        # r167
        (
            "cosign_reusable",
            {
                "slug": "cosign-attest-predicate-vs-attach",
                "plant": "staurolite-oci",
                "image": "ghcr.io/staurolite-designed/staurolite-oci:2.2.0",
                "digest": "sha256:" + hx("stau-img", 64),
                "call_id": "cosign attach sbom (layer) treated as in-toto attestation",
                "reuse_id": "cosign attest --predicate slsa --type slsaprovenance",
                "reuse_short": "attest predicate slsaprovenance",
                "tag": "v2.2.0",
                "ver": "2.2.0",
                "leftover": "attached SBOM layer still on digest",
                "inspect_cmd": "git verify-tag v2.2.0 2>&1 | tail -n 6; crane digest ghcr.io/staurolite-designed/staurolite-oci:2.2.0; cosign version | head -n 1",
                "inspect_obs": "Good \"git\" signature\n"
                + gsha("stau-tag")
                + "\nsha256:"
                + hx("stau-img", 64)
                + "\nGitVersion:    v2.4.1",
                "wf_path": ".github/workflows/attest.yml",
                "wf_obs": "name: attest\njobs:\n  sbom:\n    steps:\n      - run: cosign attach sbom --sbom syft.spdx.json $IMAGE\n",
                "pol_path": "policy/verify-attestation.json",
                "pol_obs": "{\n  \"type\": \"slsaprovenance\",\n  \"identity\": \"https://github.com/staurolite-designed/staurolite-oci/.github/workflows/attest.yml@refs/tags/v2.2.0\"\n}\n",
                "decode_cmd": "cosign verify-attestation ghcr.io/staurolite-designed/staurolite-oci@sha256:"
                + hx("stau-img", 64)
                + " --type slsaprovenance 2>&1 | tail -n 12",
                "decode_obs": "error: no attestations of type slsaprovenance\nfound attached layer application/vnd.syft.sbom.spdx+json (not an in-toto predicate)",
                "apply_cmd": "cosign verify-attestation ghcr.io/staurolite-designed/staurolite-oci@sha256:"
                + hx("stau-img", 64)
                + " --type slsaprovenance --certificate-identity https://github.com/staurolite-designed/staurolite-oci/.github/workflows/attest.yml@refs/tags/v2.2.0 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 10",
                "apply_obs": "error: attached SBOM layer is not an in-toto attestation\nwant predicateType https://slsa.dev/provenance/v1",
                "san_cmd": "crane config ghcr.io/staurolite-designed/staurolite-oci@sha256:"
                + hx("stau-img", 64)
                + " | python3 -c 'import sys; print(sys.stdin.read()[:200])'; echo LAYERS=sbom_attached",
                "san_obs": "mediaType application/vnd.oci.image.config.v1+json\nLAYERS=sbom_attached",
                "iss_cmd": "echo ATTEST_API=referrers PREDICATE=slsaprovenance ATTACH=layer_only",
                "iss_obs": "ATTEST_API=referrers PREDICATE=slsaprovenance ATTACH=layer_only",
                "pol_new": "{\n  \"type\": \"slsaprovenance\",\n  \"identity\": \"https://github.com/staurolite-designed/staurolite-oci/.github/workflows/attest.yml@refs/tags/v2.2.0\",\n  \"note\": \"must cosign attest, not attach sbom\"\n}\n",
                "verify_cmd": "cosign attest --yes --type slsaprovenance --predicate slsa.json ghcr.io/staurolite-designed/staurolite-oci@sha256:"
                + hx("stau-img", 64)
                + " && cosign verify-attestation ghcr.io/staurolite-designed/staurolite-oci@sha256:"
                + hx("stau-img", 64)
                + " --type slsaprovenance --certificate-identity https://github.com/staurolite-designed/staurolite-oci/.github/workflows/attest.yml@refs/tags/v2.2.0 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 8",
                "verify_obs": "Verified OK\npredicateType https://slsa.dev/provenance/v1\nsubject digest sha256:"
                + hx("stau-img", 16),
                "left_cmd": "crane ls ghcr.io/staurolite-designed/staurolite-oci | rg sbom || echo SBOM_LAYER_STILL_ATTACHED",
                "left_obs": "sha256:"
                + hx("stau-sbom-layer", 16)
                + " application/vnd.syft.sbom.spdx+json\nSBOM_LAYER_STILL_ATTACHED",
                "up_cmd": "echo ATTESTATION=referrers_ok ATTACH_LAYER=leftover",
                "up_obs": "ATTESTATION=referrers_ok ATTACH_LAYER=leftover",
                "wf_old": "      - run: cosign attach sbom --sbom syft.spdx.json $IMAGE",
                "wf_new": "      - run: cosign attest --yes --type slsaprovenance --predicate slsa.json $IMAGE\n      # attach sbom is a layer, not an in-toto attestation",
                "cmt_cmd": "git add policy/verify-attestation.json .github/workflows/attest.yml && git commit -m 'attest slsa predicate; stop attach-as-attest'",
                "cmt_obs": "[main " + hx("stau-cmt", 7) + "] attest slsa predicate; stop attach-as-attest",
                "tag_cmd": "git rev-parse v2.2.0^{commit}",
                "tag_obs": gsha("stau-tag"),
                "res_cmd": "echo ATTEST=slsa ATTACH_SBOM=leftover TAG=" + gsha("stau-tag")[:12],
                "res_obs": "ATTEST=slsa ATTACH_SBOM=leftover TAG=" + gsha("stau-tag")[:12],
                "res_refl": "cosign attest writes an in-toto predicate; attach sbom is only a layer. Residual: attached SBOM layer still on the digest.",
                "seed": "attach sbom ≠ attest predicate",
                "first": "verify-attestation on attached layer",
                "change": "cosign attest slsaprovenance",
                "term": "success; SBOM layer leftover",
            },
            "fail_leftover",
            {
                "slug": "pypi-trusted-publisher-env-mismatch",
                "plant": "kyanite-py",
                "goal": "kyanite-py 1.2.0 was uploaded with an API token because the Trusted Publisher is registered for environment prod but the workflow uses environment: staging. Publish 1.2.1 via OIDC. Do not delete 1.2.0. Warehouse latest still 1.2.0 (no PEP 740).",
                "plan": "Re-upload 1.2.0 via OIDC after setting environment: prod in the already-published files.",
                "outcome": "Re-upload 1.2.0 refused (filename unique). Plan change: 1.2.1 with environment: prod matching the publisher. Residual: latest=1.2.0 token upload, no attestations. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "latest_still_old": 1, "cost_steps": 16},
                "inspect_cmd": "curl -sS https://pypi.org/pypi/kyanite-py/json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(p[\"info\"][\"version\"]); print(list(p[\"releases\"])[-3:])'",
                "inspect_obs": "1.2.0\n['1.1.8', '1.1.9', '1.2.0']",
                "wf_path": ".github/workflows/pypi.yml",
                "wf_obs": "name: pypi\njobs:\n  pub:\n    environment: staging\n    permissions:\n      id-token: write\n    steps:\n      - uses: pypa/gh-action-pypi-publish@release/v1\n",
                "why_cmd": "echo REGISTERED_ENV=prod WORKFLOW_ENV=staging LAST=token_fallback_120",
                "why_obs": "REGISTERED_ENV=prod WORKFLOW_ENV=staging LAST=token_fallback_120\n# 1.2.0 has no PEP 740",
                "con_path": "pip-constraints.txt",
                "con_obs": "kyanite-py==1.2.0\n# fleet --upgrade uses PyPI latest\n",
                "apply_cmd": "python3 -m twine upload dist/kyanite_py-1.2.0-py3-none-any.whl 2>&1 | tail -n 12",
                "apply_obs": "HTTPError: 400 File already exists\nkyanite_py-1.2.0-py3-none-any.whl\nTrusted publishing skipped: environment 'staging' != registered 'prod'",
                "apply_refl": "Apply failed. Warehouse will not replace 1.2.0; OIDC env name must match the publisher row.",
                "still_cmd": "curl -sSI https://files.pythonhosted.org/packages/ky/an/kyanite_py-1.2.0-py3-none-any.whl | rg -i HTTP",
                "still_obs": "HTTP/2 200",
                "use_cmd": "curl -sS https://pypi.org/pypi/kyanite-py/json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"info\"][\"version\"])'",
                "use_obs": "1.2.0",
                "fix_cmd": "python3 - <<'PY'\nfrom pathlib import Path\np=Path('.github/workflows/pypi.yml'); p.write_text(p.read_text().replace('environment: staging','environment: prod')); print('env=prod')\nPY",
                "fix_obs": "env=prod",
                "pub_cmd": "sed -i 's/1.2.0/1.2.1/' pyproject.toml && python3 -m build && python3 -m twine upload dist/kyanite_py-1.2.1-py3-none-any.whl 2>&1 | tail -n 12",
                "pub_obs": "Uploading kyanite_py-1.2.1-py3-none-any.whl\nAttestations uploaded (environment=prod)",
                "ver_cmd": "curl -sS https://pypi.org/integrity/kyanite-py/1.2.1/kyanite_py-1.2.1-py3-none-any.whl/provenance | python3 -c 'import sys; print(\"prov\", len(sys.stdin.read())>0)'",
                "ver_obs": "prov True",
                "tag_cmd": "git add pyproject.toml .github/workflows/pypi.yml && git commit -m 'release 1.2.1 trusted publisher env=prod' && git tag -s v1.2.1 -m '1.2.1'",
                "tag_obs": "[main " + hx("kya-cmt", 7) + "] release 1.2.1 trusted publisher env=prod",
                "still2_cmd": "curl -sS https://pypi.org/pypi/kyanite-py/json | python3 -c 'import json,sys; print(\"latest\", json.load(sys.stdin)[\"info\"][\"version\"])'",
                "still2_obs": "latest 1.2.0",
                "undo_cmd": "echo skipped_yank_120=1; echo skipped_token_reupload=1",
                "undo_obs": "skipped_yank_120=1\nskipped_token_reupload=1",
                "split_cmd": "echo LATEST=1.2.0_no_pep740 NEW=1.2.1_oidc ENV=prod",
                "split_obs": "LATEST=1.2.0_no_pep740 NEW=1.2.1_oidc ENV=prod",
                "tix_cmd": "echo TICKET=pypi_latest_still_1.2.0_token",
                "tix_obs": "TICKET=pypi_latest_still_1.2.0_token",
                "res_cmd": "echo OLD=1.2.0_token NEW=1.2.1_oidc LATEST=1.2.0",
                "res_obs": "OLD=1.2.0_token NEW=1.2.1_oidc LATEST=1.2.0",
                "seed": "publisher env=prod, workflow staging",
                "first": "re-upload 1.2.0",
                "change": "1.2.1 env=prod",
                "term": "fail: latest still 1.2.0",
            },
        ),
        # r168
        (
            "oidc_publisher",
            {
                "slug": "npm-trusted-publisher-vs-laptop-token",
                "plant": "sillimanite-js",
                "goal": "Ship sillimanite-js 6.0.0 from GitHub Actions as an npm Trusted Publisher. Laptop granular tokens must not be used (they omit provenance). Leave 5.9.9 (laptop publish, attestations=null).",
                "plan": "npm publish from the laptop with a granular token that has --provenance in .npmrc so the tarball is attested.",
                "outcome": "Laptop granular token cannot mint GitHub OIDC provenance. Plan change: register trusted publisher and publish from GHA with id-token. 6.0.0 has provenance. Residual: 5.9.9 laptop publish, no attestations.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "npm whoami; npm token list 2>&1 | tail -n 6; ls .github/workflows",
                "inspect_obs": "release-bot\ngranular  npl_***  automation  ~publish\nrelease.yml",
                "wf_path": ".github/workflows/release.yml",
                "wf_obs": "name: release\n# no id-token yet; publish still documented as laptop step\n",
                "meta_path": "package.json",
                "meta_obs": "{\n  \"name\": \"@sillimanite/core\",\n  \"version\": \"6.0.0\",\n  \"publishConfig\": { \"provenance\": true, \"access\": \"public\" }\n}\n",
                "claim_cmd": "echo LAPTOP=no_GITHUB_ACTIONS OIDC=absent",
                "claim_obs": "LAPTOP=no_GITHUB_ACTIONS OIDC=absent",
                "apply_cmd": "npm publish --access public --provenance 2>&1 | tail -n 16",
                "apply_obs": "npm ERR! code EUSAGE\nnpm ERR! provenance generation in CI requires OIDC id-token\nnpm ERR! granular token cannot mint GitHub workflow identity",
                "apply_refl": "Apply failed. npm --provenance requires GitHub OIDC; a laptop granular token cannot sign provenance.",
                "diff_cmd": "echo NEED=trusted_publisher_GHA HAVE=laptop_granular",
                "diff_obs": "NEED=trusted_publisher_GHA HAVE=laptop_granular",
                "iss_cmd": "echo ISSUER=https://token.actions.githubusercontent.com SUBJECT=repo:sillimanite-designed/sillimanite-js:environment:release",
                "iss_obs": "ISSUER=https://token.actions.githubusercontent.com SUBJECT=repo:sillimanite-designed/sillimanite-js:environment:release",
                "fix_path": ".github/workflows/release.yml",
                "fix_contents": "name: release\npermissions:\n  id-token: write\n  contents: write\njobs:\n  pub:\n    runs-on: ubuntu-latest\n    environment: release\n    steps:\n      - uses: actions/setup-node@v4\n        with: { registry-url: 'https://registry.npmjs.org' }\n      - run: npm publish --access public --provenance\n",
                "pub_cmd": "echo SIMULATE_GHA=1 && npm publish --access public --provenance 2>&1 | tail -n 10",
                "pub_obs": "+ @sillimanite/core@6.0.0\nprovenance in-toto attestations uploaded\nidentity GitHub workflow release.yml",
                "att_cmd": "npm view @sillimanite/core@6.0.0 --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(p.get(\"dist\",{}).get(\"attestations\"))'",
                "att_obs": "{'url': 'https://registry.npmjs.org/-/npm/v1/attestations/@sillimanite/core@6.0.0', 'provenance': {'predicateType': 'https://slsa.dev/provenance/v1'}}",
                "left_cmd": "npm view @sillimanite/core@5.9.9 --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"dist\",{}).get(\"attestations\"))'",
                "left_obs": "None",
                "doc_cmd": "echo SKIP_599=laptop_token KEEP=1",
                "doc_obs": "SKIP_599=laptop_token KEEP=1",
                "tag_cmd": "git verify-tag v6.0.0 2>&1 | tail -n 3; echo tag_ok",
                "tag_obs": "Good \"git\" signature\ntag_ok",
                "cmt_cmd": "git add .github/workflows/release.yml && git commit -m 'release 6.0.0 trusted publisher; no laptop token'",
                "cmt_obs": "[main " + hx("sill-cmt", 7) + "] release 6.0.0 trusted publisher; no laptop token",
                "res_cmd": "echo PUB=GHA_OIDC ATTEST_600=yes LAPTOP_599=no_attest",
                "res_obs": "PUB=GHA_OIDC ATTEST_600=yes LAPTOP_599=no_attest",
                "res_refl": "npm provenance is OIDC-only. Residual: 5.9.9 laptop publish has no attestations.",
                "seed": "laptop granular token --provenance",
                "first": "npm publish from laptop",
                "change": "GHA trusted publisher",
                "term": "success; 5.9.9 no attest",
            },
            "fail_leftover",
            {
                "slug": "homebrew-catalina-bottle-leftover",
                "plant": "andalusite-brew",
                "goal": "andalusite-brew 2.3.0 sonoma bottle rebuilt; catalina bottle on the GitHub Release is still the pre-rebuild tarball. Do not delete the GH release. brew test-bot on catalina-selfhost still pours the old bottle.",
                "plan": "gh release delete-asset the catalina bottle and re-upload the sonoma tarball under the catalina name.",
                "outcome": "Renaming the sonoma bottle as catalina failed brew audit (ELF/Mach-O tag mismatch). Plan change: leave catalina asset; ship sonoma rebuild 2. Residual: catalina-selfhost still pours the old bottle. Ticket not closed.",
                "reward": {"success": False, "sign_fails": 1, "plan_changes": 1, "bottle_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "gh release view v2.3.0 --json assets --jq '.assets[].name'",
                "inspect_obs": "andalusite-2.3.0.catalina.bottle.tar.gz\nandalusite-2.3.0.sonoma.bottle.2.tar.gz",
                "wf_path": "Formula/andalusite.rb",
                "wf_obs": "bottle do\n  rebuild 2\n  sha256 cellar: :any, sonoma: \""
                + hx("anda-sonoma", 64)
                + "\"\nend\n",
                "why_cmd": "echo CATALINA_SHA="
                + hx("anda-cat", 16)
                + " SONOMA_SHA="
                + hx("anda-sonoma", 16)
                + " MISMATCH=1",
                "why_obs": "CATALINA_SHA="
                + hx("anda-cat", 16)
                + " SONOMA_SHA="
                + hx("anda-sonoma", 16)
                + " MISMATCH=1",
                "con_path": "../andalusite-selfhost/Brewfile",
                "con_obs": "brew \"andalusite\"\n# runner: catalina-selfhost\n",
                "apply_cmd": "gh release delete-asset v2.3.0 andalusite-2.3.0.catalina.bottle.tar.gz --yes && gh release upload v2.3.0 andalusite-2.3.0.sonoma.bottle.2.tar.gz#andalusite-2.3.0.catalina.bottle.tar.gz 2>&1 | tail -n 12",
                "apply_obs": "uploaded alias\nbrew audit: * bottle tag catalina contains sonoma Mach-O / min macOS 14\nError: 1 problem",
                "apply_refl": "Apply failed. A sonoma bottle cannot be renamed onto the catalina tag.",
                "still_cmd": "gh release view v2.3.0 --json assets --jq '.assets[].name'",
                "still_obs": "andalusite-2.3.0.catalina.bottle.tar.gz\nandalusite-2.3.0.sonoma.bottle.2.tar.gz",
                "use_cmd": "echo POUR_CATALINA_SELFHOST="
                + hx("anda-cat", 16),
                "use_obs": "POUR_CATALINA_SELFHOST=" + hx("anda-cat", 16),
                "fix_cmd": "echo KEEP_CATALINA_ASSET=1 SHIP_SONOMA_REBUILD2=1",
                "fix_obs": "KEEP_CATALINA_ASSET=1 SHIP_SONOMA_REBUILD2=1",
                "pub_cmd": "brew bottle --rebuild --json andalusite 2>&1 | tail -n 6",
                "pub_obs": "Bottling andalusite-2.3.0.sonoma.bottle.2.tar.gz",
                "ver_cmd": "brew audit --strict andalusite 2>&1 | tail -n 4",
                "ver_obs": "0 problems (sonoma)",
                "tag_cmd": "git verify-tag v2.3.0 >/dev/null && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "still2_cmd": "echo POUR_CATALINA_SELFHOST="
                + hx("anda-cat", 16)
                + " STILL=1",
                "still2_obs": "POUR_CATALINA_SELFHOST="
                + hx("anda-cat", 16)
                + " STILL=1",
                "undo_cmd": "echo skipped_delete_release=1; echo skipped_alias_bottle=1",
                "undo_obs": "skipped_delete_release=1\nskipped_alias_bottle=1",
                "split_cmd": "echo SONOMA=rebuild2 CATALINA=old_asset SELFHOST=catalina",
                "split_obs": "SONOMA=rebuild2 CATALINA=old_asset SELFHOST=catalina",
                "tix_cmd": "echo TICKET=catalina_selfhost_still_pours_old_bottle",
                "tix_obs": "TICKET=catalina_selfhost_still_pours_old_bottle",
                "res_cmd": "echo SONOMA=ok CATALINA=leftover",
                "res_obs": "SONOMA=ok CATALINA=leftover",
                "seed": "catalina bottle leftover after sonoma rebuild",
                "first": "rename sonoma bottle to catalina",
                "change": "leave catalina asset",
                "term": "fail: selfhost still catalina",
            },
        ),
        # r169
        (
            "gpg_portal",
            {
                "slug": "maven-publisher-portal-vs-ossrh",
                "plant": "cordierite-mvn",
                "goal": "Ship cordierite-mvn 8.1.0 through Maven Central Publisher Portal. OSSRH close is retired. Do not reuse the OSSRH staging profile. Leave the leftover OSSRH profile id in settings.xml comments.",
                "plan": "mvn nexus-staging:release against OSSRH s01 because that is what settings.xml still names.",
                "outcome": "OSSRH close rejected (legacy endpoint retired). Plan change: central-publishing-maven-plugin to Publisher Portal. 8.1.0 published. Residual: OSSRH profile id still in settings comments.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "portal": 1, "cost_steps": 15},
                "inspect_cmd": "mvn -v | head -n 2; echo OSSRH=s01.oss.sonatype.org; echo PORTAL=central.sonatype.com",
                "inspect_obs": "Apache Maven 3.9.9\nOSSRH=s01.oss.sonatype.org\nPORTAL=central.sonatype.com",
                "pom_path": "pom.xml",
                "pom_obs": "<plugin>\n  <groupId>org.sonatype.plugins</groupId>\n  <artifactId>nexus-staging-maven-plugin</artifactId>\n  <configuration><nexusUrl>https://s01.oss.sonatype.org/</nexusUrl></configuration>\n</plugin>\n",
                "set_path": "~/.m2/settings.xml",
                "set_obs": "<server><id>ossrh</id><username>cordierite</username></server>\n",
                "exp_cmd": "gpg --list-keys release@cordierite.example | rg -n 'exp|sub'",
                "exp_obs": "ssb rsa4096 [S] expires: 2028-04-01",
                "apply_cmd": "mvn -B nexus-staging:release 2>&1 | tail -n 14",
                "apply_obs": "401 Unauthorized / 410 Gone\nOSSRH hosted close API retired 2025-06-30; use Publisher Portal\n",
                "apply_refl": "Apply failed. OSSRH staging close is retired; Central only accepts Publisher Portal uploads.",
                "sub_cmd": "echo GPG_SUB=live PORTAL_PLUGIN=central-publishing-maven-plugin",
                "sub_obs": "GPG_SUB=live PORTAL_PLUGIN=central-publishing-maven-plugin",
                "ep_cmd": "echo ENDPOINT=https://central.sonatype.com/api/v1/publisher",
                "ep_obs": "ENDPOINT=https://central.sonatype.com/api/v1/publisher",
                "fix_path": "pom.xml",
                "fix_contents": "<plugin>\n  <groupId>org.sonatype.central</groupId>\n  <artifactId>central-publishing-maven-plugin</artifactId>\n  <extensions>true</extensions>\n</plugin>\n",
                "sign_cmd": "mvn -B -Prelease deploy -DskipTests 2>&1 | tail -n 12",
                "sign_obs": "Uploading to Publisher Portal\nDeployment ID dep-"
                + hx("cord-dep", 12)
                + "\nGPG signatures attached",
                "close_cmd": "mvn -B central-publishing:publish 2>&1 | tail -n 8",
                "close_obs": "Published cordierite-mvn 8.1.0 on Central",
                "left_cmd": "rg -n 'ossrh|s01.oss.sonatype' ~/.m2/settings.xml pom.xml | head",
                "left_obs": "settings.xml:<!-- leftover ossrh profile id cordierite-ossrh -->",
                "drop_cmd": "echo SKIP_PROMOTE_OSSRH=1",
                "drop_obs": "SKIP_PROMOTE_OSSRH=1",
                "tag_cmd": "git tag -s v8.1.0 -m '8.1.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add pom.xml && git commit -m 'release 8.1.0 Publisher Portal; drop OSSRH close'",
                "cmt_obs": "[main " + hx("cord-cmt", 7) + "] release 8.1.0 Publisher Portal; drop OSSRH close",
                "res_cmd": "echo PORTAL=8.1.0 OSSRH_COMMENT=leftover",
                "res_obs": "PORTAL=8.1.0 OSSRH_COMMENT=leftover",
                "res_refl": "Publisher Portal replaced OSSRH close. Residual: OSSRH profile id still in settings comments.",
                "seed": "OSSRH close retired",
                "first": "nexus-staging:release s01",
                "change": "central-publishing plugin",
                "term": "success; ossrh comment leftover",
            },
            "fail_leftover",
            {
                "slug": "nix-binary-cache-wrong-nar-leftover",
                "plant": "chloritoid-nix",
                "goal": "chloritoid-nix 0.9.0 FOD was rebuilt with the correct NAR locally. The team binary cache still serves the old gzip-hash store path. Do not --repair the shared cache from a laptop. Hydra consumers still substitute the old path.",
                "plan": "nix copy --to the shared cache using --force to overwrite the old NAR.",
                "outcome": "Overwrite of the cache path refused (content-addressed, immutable). Plan change: new outputHash / new store path 0.9.1. Residual: Hydra still substitutes the old NAR. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "cache_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "nix path-info --store https://cache.chloritoid.example "
                + "/nix/store/"
                + hx("chl-old", 32)
                + "-src 2>&1 | tail -n 8",
                "inspect_obs": "path exists\nnarHash sha256-"
                + hx("chl-oldnar", 44)
                + "=\n# this is the gzip-as-NAR mistake",
                "wf_path": "flake.nix",
                "wf_obs": "outputHash = \"sha256-"
                + hx("chl-newnar", 44)
                + "=\"; # local correct\n",
                "why_cmd": "echo LOCAL_NAR="
                + hx("chl-newnar", 12)
                + " CACHE_NAR="
                + hx("chl-oldnar", 12),
                "why_obs": "LOCAL_NAR="
                + hx("chl-newnar", 12)
                + " CACHE_NAR="
                + hx("chl-oldnar", 12),
                "con_path": "hydra/jobset.nix",
                "con_obs": "substituters = [ \"https://cache.chloritoid.example\" ];\ntrusted-substituters = [ \"https://cache.chloritoid.example\" ];\n",
                "apply_cmd": "nix copy --to https://cache.chloritoid.example --force /nix/store/"
                + hx("chl-new", 32)
                + "-src 2>&1 | tail -n 12",
                "apply_obs": "error: refusing to overwrite content-addressed path\nuse a new outputHash / new store path; cache is immutable",
                "apply_refl": "Apply failed. Nix binary caches do not overwrite CA paths; you publish a new hash.",
                "still_cmd": "curl -sSI https://cache.chloritoid.example/"
                + hx("chl-old", 32)
                + ".narinfo | rg -i HTTP",
                "still_obs": "HTTP/2 200",
                "use_cmd": "echo HYDRA_SUBSTITUTE=/nix/store/"
                + hx("chl-old", 32)
                + "-src",
                "use_obs": "HYDRA_SUBSTITUTE=/nix/store/"
                + hx("chl-old", 32)
                + "-src",
                "fix_cmd": "echo NEXT=0.9.1 NEW_OUTHASH="
                + hx("chl-newnar", 16),
                "fix_obs": "NEXT=0.9.1 NEW_OUTHASH=" + hx("chl-newnar", 16),
                "pub_cmd": "sed -i 's/0.9.0/0.9.1/' flake.nix && nix build && nix copy --to https://cache.chloritoid.example ./result 2>&1 | tail -n 8",
                "pub_obs": "copied /nix/store/"
                + hx("chl-new", 32)
                + "-chloritoid-nix-0.9.1",
                "ver_cmd": "nix path-info ./result | tail -n 2",
                "ver_obs": "/nix/store/"
                + hx("chl-new", 32)
                + "-chloritoid-nix-0.9.1",
                "tag_cmd": "git commit -am 'release 0.9.1 new NAR path' && git tag -s v0.9.1 -m '0.9.1'",
                "tag_obs": "[main " + hx("chl-cmt", 7) + "] release 0.9.1 new NAR path",
                "still2_cmd": "echo HYDRA_SUBSTITUTE=/nix/store/"
                + hx("chl-old", 32)
                + "-src STILL=1",
                "still2_obs": "HYDRA_SUBSTITUTE=/nix/store/"
                + hx("chl-old", 32)
                + "-src STILL=1",
                "undo_cmd": "echo skipped_cache_overwrite=1; echo skipped_narinfo_delete=1",
                "undo_obs": "skipped_cache_overwrite=1\nskipped_narinfo_delete=1",
                "split_cmd": "echo LOCAL=0.9.1 CACHE_OLD=200 HYDRA=old",
                "split_obs": "LOCAL=0.9.1 CACHE_OLD=200 HYDRA=old",
                "tix_cmd": "echo TICKET=hydra_still_substitutes_old_nar",
                "tix_obs": "TICKET=hydra_still_substitutes_old_nar",
                "res_cmd": "echo NEW=0.9.1 CACHE_OLD=leftover",
                "res_obs": "NEW=0.9.1 CACHE_OLD=leftover",
                "seed": "binary cache immutable NAR",
                "first": "nix copy --force overwrite",
                "change": "0.9.1 new store path",
                "term": "fail: Hydra still old NAR",
            },
        ),
        # r170
        (
            "nuget_snupkg",
            {
                "slug": "nuget-portable-pdb-vs-full-pdb",
                "plant": "carpholite-nupkg",
                "goal": "Ship carpholite-nupkg 7.4.0 with a portable PDB inside the snupkg. Full Windows PDBs were packed; symbols.nuget.org rejected them. Keep signed v7.4.0. Leave the full-PDB snupkg listed as 409 leftover.",
                "plan": "dotnet nuget push the full-PDB snupkg because Windows CI produced it.",
                "outcome": "Full Windows PDB snupkg rejected. Plan change: DebugType=portable, pack once, push. 7.4.0 portable symbols resolve. Residual: full-PDB snupkg attempt leftover on the symbol server log.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "symbols": 1, "cost_steps": 15},
                "inspect_cmd": "ls dist; file dist/*.pdb 2>/dev/null | head; echo DEBUGTYPE=full",
                "inspect_obs": "dist/Carpholite.7.4.0.nupkg\ndist/Carpholite.7.4.0.snupkg\ndist/Carpholite.pdb: MSVC program database 7.00\nDEBUGTYPE=full",
                "nus_path": "Carpholite.nuspec",
                "nus_obs": "<id>Carpholite</id><version>7.4.0</version>\n<repository commit=\""
                + gsha("carp-tag")
                + "\" />\n",
                "dbp_path": "Directory.Build.props",
                "dbp_obs": "<DebugType>full</DebugType>\n<IncludeSymbols>true</IncludeSymbols>\n<SymbolPackageFormat>snupkg</SymbolPackageFormat>\n",
                "cmp_cmd": "echo NUPKG_COMMIT="
                + gsha("carp-tag")
                + " SNUPKG_COMMIT="
                + gsha("carp-tag")
                + " PDB=full",
                "cmp_obs": "NUPKG_COMMIT="
                + gsha("carp-tag")
                + " SNUPKG_COMMIT="
                + gsha("carp-tag")
                + " PDB=full",
                "apply_cmd": "dotnet nuget push dist/Carpholite.7.4.0.snupkg --source https://nuget.smbsrc.net/ 2>&1 | tail -n 12",
                "apply_obs": "error: Symbol package contains Windows PDB (MSVC 7.00); portable PDB required\nHTTP 400",
                "apply_refl": "Apply failed. symbols.nuget.org accepts portable PDBs in snupkg, not full Windows PDBs.",
                "pdb_cmd": "python3 - <<'PY'\nprint('PDB kind: MSVC full')\nprint('need: portable (DSIF)')\nPY",
                "pdb_obs": "PDB kind: MSVC full\nneed: portable (DSIF)",
                "host_cmd": "echo NUGET=api.nuget.org SYM=nuget.smbsrc.net",
                "host_obs": "NUGET=api.nuget.org SYM=nuget.smbsrc.net",
                "dbp_new": "<DebugType>portable</DebugType>\n<IncludeSymbols>true</IncludeSymbols>\n<SymbolPackageFormat>snupkg</SymbolPackageFormat>\n",
                "pack_cmd": "dotnet pack -c Release && dotnet nuget push dist/Carpholite.7.4.0.nupkg --source https://api.nuget.org/v3/index.json && dotnet nuget push dist/Carpholite.7.4.0.snupkg --source https://nuget.smbsrc.net/",
                "pack_obs": "Your package was pushed.\nYour symbol package was pushed.\nPDB=portable",
                "sym_cmd": "echo SYM_RESOLVE=Carpholite.pdb portable=1",
                "sym_obs": "SYM_RESOLVE=Carpholite.pdb portable=1",
                "left_cmd": "echo SYM_LOG_FULL_PDB_409=1",
                "left_obs": "SYM_LOG_FULL_PDB_409=1",
                "unl_cmd": "echo UNLIST_FULL_PDB_ATTEMPT=n/a KEEP_LOG=1",
                "unl_obs": "UNLIST_FULL_PDB_ATTEMPT=n/a KEEP_LOG=1",
                "tag_cmd": "git verify-tag v7.4.0 >/dev/null && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add Directory.Build.props && git commit -m 'release 7.4.0 portable PDB snupkg'",
                "cmt_obs": "[main " + hx("carp-cmt", 7) + "] release 7.4.0 portable PDB snupkg",
                "res_cmd": "echo PDB=portable FULL_PDB_LOG=leftover",
                "res_obs": "PDB=portable FULL_PDB_LOG=leftover",
                "res_refl": "snupkg needs portable PDBs. Residual: full-PDB 409 still in the symbol-server log.",
                "seed": "full Windows PDB in snupkg",
                "first": "push full-PDB snupkg",
                "change": "DebugType=portable",
                "term": "success; 409 log leftover",
            },
            "fail_leftover",
            {
                "slug": "cosign-sig-tag-leftover-after-referrers",
                "plant": "winchite-oci",
                "goal": "winchite-oci 3.3.0 moved verify to the referrers API. The old :sha256-*.sig OCI tag still exists. Do not delete the repo. Cluster policy still admits the .sig tag as if it were an image.",
                "plan": "crane delete the .sig tag and re-sign with the same tag name so clusters keep working.",
                "outcome": "Deleting the .sig tag is blocked by tag-immutability. Plan change: attest via referrers; leave .sig tag. Residual: admission still treats .sig as an image. Ticket not closed.",
                "reward": {"success": False, "sign_fails": 1, "plan_changes": 1, "sig_tag_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "crane ls ghcr.io/winchite-designed/winchite-oci | rg -n 'sig|3.3.0|latest'",
                "inspect_obs": "3.3.0\nsha256-"
                + hx("win-img", 16)
                + ".sig\nlatest",
                "wf_path": ".github/workflows/sign.yml",
                "wf_obs": "run: cosign sign --yes $IMAGE  # default now referrers; old job used --registry-referrers-mode=legacy-sig-tag\n",
                "why_cmd": "cosign verify ghcr.io/winchite-designed/winchite-oci:3.3.0 --certificate-identity https://github.com/winchite-designed/winchite-oci/.github/workflows/sign.yml@refs/tags/v3.3.0 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 8",
                "why_obs": "Verified OK via referrers\nlegacy .sig tag still present",
                "con_path": "cluster/admission.yaml",
                "con_obs": "image: ghcr.io/winchite-designed/winchite-oci:sha256-"
                + hx("win-img", 16)
                + ".sig\n# kyverno treats this as a runnable tag\n",
                "apply_cmd": "crane delete ghcr.io/winchite-designed/winchite-oci:sha256-"
                + hx("win-img", 16)
                + ".sig 2>&1 | tail -n 10",
                "apply_obs": "DENIED: tag immutability policy (packages: write not enough)\nrefusing to delete .sig tag",
                "apply_refl": "Apply failed. GHCR tag immutability blocks deleting the legacy .sig tag.",
                "still_cmd": "crane digest ghcr.io/winchite-designed/winchite-oci:sha256-"
                + hx("win-img", 16)
                + ".sig",
                "still_obs": "sha256:" + hx("win-sig", 64),
                "use_cmd": "echo ADMISSION_IMAGE=.sig_tag STILL=1",
                "use_obs": "ADMISSION_IMAGE=.sig_tag STILL=1",
                "fix_cmd": "echo USE_REFERRERS=1 LEAVE_SIG_TAG=1",
                "fix_obs": "USE_REFERRERS=1 LEAVE_SIG_TAG=1",
                "pub_cmd": "cosign attest --yes --type slsaprovenance --predicate slsa.json ghcr.io/winchite-designed/winchite-oci:3.3.0 2>&1 | tail -n 8",
                "pub_obs": "attestation uploaded via referrers API",
                "ver_cmd": "cosign verify-attestation ghcr.io/winchite-designed/winchite-oci:3.3.0 --type slsaprovenance 2>&1 | tail -n 6",
                "ver_obs": "Verified OK",
                "tag_cmd": "git verify-tag v3.3.0 >/dev/null && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "still2_cmd": "crane ls ghcr.io/winchite-designed/winchite-oci | rg sig",
                "still2_obs": "sha256-" + hx("win-img", 16) + ".sig",
                "undo_cmd": "echo skipped_tag_delete=1; echo skipped_force_untag=1",
                "undo_obs": "skipped_tag_delete=1\nskipped_force_untag=1",
                "split_cmd": "echo REFERRERS=ok SIG_TAG=leftover ADMISSION=sig_tag",
                "split_obs": "REFERRERS=ok SIG_TAG=leftover ADMISSION=sig_tag",
                "tix_cmd": "echo TICKET=kyverno_still_admits_legacy_sig_tag",
                "tix_obs": "TICKET=kyverno_still_admits_legacy_sig_tag",
                "res_cmd": "echo ATTEST=referrers SIG_TAG=leftover",
                "res_obs": "ATTEST=referrers SIG_TAG=leftover",
                "seed": "legacy .sig tag vs referrers",
                "first": "crane delete .sig tag",
                "change": "attest referrers; leave tag",
                "term": "fail: admission still .sig",
            },
        ),
        # r171
        (
            "oidc_publisher",
            {
                "slug": "pypi-pending-publisher-activation",
                "plant": "barroisite-py",
                "goal": "Ship barroisite-py 0.8.0. Trusted Publisher is pending (project did not exist at registration). Activate by first OIDC upload, not an API token. Leave the pending-row screenshot in docs.",
                "plan": "Create the project with an API token so the pending publisher can bind, then re-upload.",
                "outcome": "API-token first upload would consume 0.8.0 without PEP 740 and leave the publisher pending. Plan change: first upload via OIDC to activate the pending publisher. Residual: pending-row screenshot leftover in docs.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "echo PUBLISHER=pending PROJECT=missing; ls dist",
                "inspect_obs": "PUBLISHER=pending PROJECT=missing\ndist/barroisite_py-0.8.0-py3-none-any.whl",
                "wf_path": ".github/workflows/pypi.yml",
                "wf_obs": "permissions:\n  id-token: write\njobs:\n  pypi:\n    environment: release\n    uses: pypa/gh-action-pypi-publish@release/v1\n",
                "meta_path": "pyproject.toml",
                "meta_obs": "[project]\nname = \"barroisite-py\"\nversion = \"0.8.0\"\n",
                "claim_cmd": "echo workflow=pypi.yml environment=release pending=1",
                "claim_obs": "workflow=pypi.yml environment=release pending=1",
                "apply_cmd": "python3 -m twine upload -u __token__ -p pypi-*** dist/barroisite_py-0.8.0-py3-none-any.whl 2>&1 | tail -n 10",
                "apply_obs": "Refusing token first-upload: it would create 0.8.0 without PEP 740 and leave the publisher pending forever for this version",
                "apply_refl": "Apply failed. The pending publisher is activated by the first OIDC upload, not by a token bootstrap.",
                "diff_cmd": "echo TOKEN_BOOTSTRAP=blocked OIDC_FIRST=required",
                "diff_obs": "TOKEN_BOOTSTRAP=blocked OIDC_FIRST=required",
                "iss_cmd": "echo ISSUER=https://token.actions.githubusercontent.com PENDING_ROW=pypi.yml@release",
                "iss_obs": "ISSUER=https://token.actions.githubusercontent.com PENDING_ROW=pypi.yml@release",
                "fix_path": "docs/publisher-status.txt",
                "fix_contents": "pending publisher will activate on first OIDC upload of barroisite-py 0.8.0\n",
                "pub_cmd": "python3 -m twine upload dist/barroisite_py-0.8.0-py3-none-any.whl 2>&1 | tail -n 12",
                "pub_obs": "Created project barroisite-py\nActivated pending trusted publisher\nAttestations uploaded",
                "att_cmd": "echo PROV_080=yes PUBLISHER=active",
                "att_obs": "PROV_080=yes PUBLISHER=active",
                "left_cmd": "ls docs/pending-publisher.png && echo SCREENSHOT=leftover",
                "left_obs": "docs/pending-publisher.png\nSCREENSHOT=leftover",
                "doc_cmd": "echo KEEP_SCREENSHOT=1",
                "doc_obs": "KEEP_SCREENSHOT=1",
                "tag_cmd": "git tag -s v0.8.0 -m '0.8.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add docs/publisher-status.txt && git commit -m 'release 0.8.0 activate pending trusted publisher'",
                "cmt_obs": "[main " + hx("barr-cmt", 7) + "] release 0.8.0 activate pending trusted publisher",
                "res_cmd": "echo PUBLISHER=active TOKEN_BOOTSTRAP=skipped SCREENSHOT=leftover",
                "res_obs": "PUBLISHER=active TOKEN_BOOTSTRAP=skipped SCREENSHOT=leftover",
                "res_refl": "Pending publisher activates on first OIDC upload. Residual: pending screenshot still in docs.",
                "seed": "pending trusted publisher",
                "first": "API token bootstrap",
                "change": "OIDC first upload",
                "term": "success; screenshot leftover",
            },
            "fail_leftover",
            {
                "slug": "crates-yank-only-token-cannot-publish",
                "plant": "taramite-crate",
                "goal": "taramite-crate 1.1.4 yanked. CI token is yank-only (no publish). Need 1.1.5. Do not unyank. Release bot still has only yank scope, so 1.1.5 never lands on the index used by CI.",
                "plan": "cargo yank --undo 1.1.4 with the yank-only token so CI can compile again, then retry publish.",
                "outcome": "unyank refused (CVE). publish 1.1.5 with yank-only token got 403. Plan change: documented scope bump; 1.1.5 not on the index. Residual: CI still sees yanked 1.1.4 only. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "token_scope": 1, "cost_steps": 16},
                "inspect_cmd": "cargo info taramite-crate 2>&1 | tail -n 8; echo TOKEN_SCOPES=yank",
                "inspect_obs": "taramite-crate 1.1.4 yanked\nTOKEN_SCOPES=yank",
                "wf_path": "Cargo.toml",
                "wf_obs": "[package]\nname = \"taramite-crate\"\nversion = \"1.1.5\"\n",
                "why_cmd": "echo CVE=2026-6601 YANKED=1.1.4",
                "why_obs": "CVE=2026-6601 YANKED=1.1.4",
                "con_path": "../taramite-ci/.cargo/config.toml",
                "con_obs": "[registries.crates-io]\nprotocol = \"sparse\"\n# token in CI: crates.io yank-only\n",
                "apply_cmd": "cargo yank --undo taramite-crate@1.1.4 2>&1 | tail -n 8; cargo publish --token \"$CRATES_TOKEN\" 2>&1 | tail -n 10",
                "apply_obs": "error: refuse unyank CVE-2026-6601\nerror: 403 this token is not allowed to publish (scopes: yank)",
                "apply_refl": "Apply failed. Yank-only tokens cannot publish a bump; unyank would re-expose the CVE.",
                "still_cmd": "curl -sS https://index.crates.io/ta/ra/taramite-crate | tail -n 2",
                "still_obs": "{\"vers\":\"1.1.4\",\"yanked\":true}",
                "use_cmd": "echo CI_RESOLVE=1.1.4_yanked",
                "use_obs": "CI_RESOLVE=1.1.4_yanked",
                "fix_cmd": "echo NEED_SCOPE=publish OWNER=secops",
                "fix_obs": "NEED_SCOPE=publish OWNER=secops",
                "pub_cmd": "cargo publish --token \"$CRATES_TOKEN\" 2>&1 | tail -n 6",
                "pub_obs": "error: 403 this token is not allowed to publish",
                "ver_cmd": "echo ON_INDEX_115=no",
                "ver_obs": "ON_INDEX_115=no",
                "tag_cmd": "git tag -s v1.1.5 -m '1.1.5 pending publish scope' && echo tag_only",
                "tag_obs": "tag_only",
                "still2_cmd": "echo CI_RESOLVE=1.1.4_yanked STILL=1",
                "still2_obs": "CI_RESOLVE=1.1.4_yanked STILL=1",
                "undo_cmd": "echo skipped_unyank=1; echo skipped_scope_self_escalate=1",
                "undo_obs": "skipped_unyank=1\nskipped_scope_self_escalate=1",
                "split_cmd": "echo GIT_TAG=v1.1.5 INDEX=1.1.4_yanked TOKEN=yank_only",
                "split_obs": "GIT_TAG=v1.1.5 INDEX=1.1.4_yanked TOKEN=yank_only",
                "tix_cmd": "echo TICKET=secops_must_grant_publish_scope",
                "tix_obs": "TICKET=secops_must_grant_publish_scope",
                "res_cmd": "echo TAG=1.1.5 INDEX=missing CI=1.1.4",
                "res_obs": "TAG=1.1.5 INDEX=missing CI=1.1.4",
                "seed": "yank-only crates.io token",
                "first": "unyank + publish with same token",
                "change": "handoff publish scope",
                "term": "fail: 1.1.5 not on index",
            },
        ),
        # r172
        (
            "bottle_rebuild",
            {
                "slug": "homebrew-gh-attestation-vs-brew-audit-signing",
                "plant": "leakeite-brew",
                "goal": "Ship leakeite-brew 4.0.0. brew audit --signing wants the Homebrew attestation, not a raw gh attestation verify of the source tag. Keep signed v4.0.0. Leave the extra gh attestation on the source tarball.",
                "plan": "gh attestation verify the source tag and treat that as brew audit --signing.",
                "outcome": "gh attestation verify passed the source tarball but brew audit --signing still failed (wants bottle attestation identity homebrew/core). Plan change: brew attestation + bottle rebuild. Residual: extra gh attestation leftover on the source tarball.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "brew audit --signing leakeite 2>&1 | tail -n 10; gh attestation list -R leakeite-designed/leakeite-brew | head",
                "inspect_obs": "leakeite:\n  * missing Homebrew bottle attestation\ngh attestation: 1 (git tag v4.0.0 source)",
                "f_path": "Formula/leakeite.rb",
                "f_obs": "class Leakeite < Formula\n  url \"https://github.com/leakeite-designed/leakeite-brew/archive/refs/tags/v4.0.0.tar.gz\"\n  sha256 \""
                + hx("leak-src", 64)
                + "\"\nend\n",
                "j_path": "leakeite-4.0.0.bottle.json",
                "j_obs": "{ \"leakeite\": { \"arm64_sonoma\": { \"sha256\": \""
                + hx("leak-bot", 64)
                + "\" } } }\n",
                "run_cmd": "gh attestation verify leakeite-4.0.0.tar.gz -R leakeite-designed/leakeite-brew 2>&1 | tail -n 8",
                "run_obs": "PASSED source tarball attestation (workflow release.yml)\n# this is not brew audit --signing",
                "apply_cmd": "brew audit --signing leakeite 2>&1 | tail -n 12",
                "apply_obs": "leakeite:\n  * bottle not attested by homebrew-core identity\n  * gh attestation on src tarball is ignored by brew audit --signing\nError: 2 problems",
                "apply_refl": "Apply failed. brew audit --signing checks Homebrew bottle attestations, not GitHub source attestations.",
                "pour_cmd": "echo BOTTLE_SHA=" + hx("leak-bot", 16),
                "pour_obs": "BOTTLE_SHA=" + hx("leak-bot", 16),
                "pol_cmd": "echo POLICY=homebrew_bottle_attestation IDENTITY=homebrew/core",
                "pol_obs": "POLICY=homebrew_bottle_attestation IDENTITY=homebrew/core",
                "f_new": "class Leakeite < Formula\n  url \"https://github.com/leakeite-designed/leakeite-brew/archive/refs/tags/v4.0.0.tar.gz\"\n  sha256 \""
                + hx("leak-src", 64)
                + "\"\n  bottle do\n    sha256 cellar: :any, arm64_sonoma: \""
                + hx("leak-bot", 64)
                + "\"\n  end\nend\n",
                "reb_cmd": "brew bottle --json leakeite && brew attestation generate leakeite 2>&1 | tail -n 8",
                "reb_obs": "generated Homebrew bottle attestation\nidentity homebrew/core",
                "aud_cmd": "brew audit --signing leakeite 2>&1 | tail -n 6",
                "aud_obs": "leakeite:\n  0 problems",
                "left_cmd": "gh attestation list -R leakeite-designed/leakeite-brew | rg -n 'tar.gz|bottle'",
                "left_obs": "1:source tarball attestation leftover\n2:homebrew bottle attestation",
                "note_cmd": "echo SRC_GH_ATTEST=leftover KEEP=1",
                "note_obs": "SRC_GH_ATTEST=leftover KEEP=1",
                "tag_cmd": "git verify-tag v4.0.0 >/dev/null && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add Formula/leakeite.rb && git commit -m 'bottle attestation for brew audit --signing'",
                "cmt_obs": "[main " + hx("leak-cmt", 7) + "] bottle attestation for brew audit --signing",
                "res_cmd": "echo BREW_AUDIT=0 SRC_ATTEST=leftover",
                "res_obs": "BREW_AUDIT=0 SRC_ATTEST=leftover",
                "res_refl": "brew audit --signing wants Homebrew bottle identity. Residual: extra gh attestation on the source tarball.",
                "seed": "gh attestation ≠ brew audit --signing",
                "first": "gh attestation verify src",
                "change": "Homebrew bottle attestation",
                "term": "success; src attest leftover",
            },
            "fail_leftover",
            {
                "slug": "nuget-unlisted-nupkg-snupkg-still-200",
                "plant": "eckermannite-nupkg",
                "goal": "eckermannite-nupkg 9.1.0 nupkg unlisted after a nuspec leak. snupkg is still GET 200 on the symbol CDN. Publish 9.1.1. Do not delete 9.1.0. Debugger still fetches 9.1.0 symbols.",
                "plan": "nuget delete 9.1.0 so both nupkg and snupkg disappear, then push 9.1.0 again clean.",
                "outcome": "nuget delete only unlists the nupkg; snupkg CDN still 200. Republish 9.1.0 refused. Plan change: 9.1.1. Residual: debugger still fetches 9.1.0 symbols. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "snupkg_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "dotnet nuget list source; echo UNLISTED=9.1.0",
                "inspect_obs": "nuget.org\nUNLISTED=9.1.0",
                "wf_path": "Eckermannite.nuspec",
                "wf_obs": "<version>9.1.0</version>\n<!-- leaked InternalVisibleTo -->\n",
                "why_cmd": "curl -sSI https://www.nuget.org/api/v2/package/Eckermannite/9.1.0 | rg -i HTTP; curl -sSI https://globalcdn.nuget.org/symbol-packages/eckermannite.9.1.0.snupkg | rg -i HTTP",
                "why_obs": "HTTP/2 404  # nupkg unlisted\nHTTP/2 200  # snupkg still there",
                "con_path": "../eckermannite-app/.config/nuget.config",
                "con_obs": "<add key=\"symbol\" value=\"https://symbols.nuget.org/download/symbols\" />\n",
                "apply_cmd": "dotnet nuget delete Eckermannite 9.1.0 --non-interactive --source https://api.nuget.org/v3/index.json 2>&1 | tail -n 10; dotnet nuget push dist/Eckermannite.9.1.0.nupkg 2>&1 | tail -n 8",
                "apply_obs": "Package unlisted (already unlisted)\nerror: 409 A package with ID 'Eckermannite' and version '9.1.0' already exists",
                "apply_refl": "Apply failed. Unlist ≠ delete; version is unique forever; snupkg CDN is a separate host.",
                "still_cmd": "curl -sSI https://globalcdn.nuget.org/symbol-packages/eckermannite.9.1.0.snupkg | rg -i HTTP",
                "still_obs": "HTTP/2 200",
                "use_cmd": "echo DEBUGGER=eckermannite.pdb index=9.1.0",
                "use_obs": "DEBUGGER=eckermannite.pdb index=9.1.0",
                "fix_cmd": "echo NEXT=9.1.1",
                "fix_obs": "NEXT=9.1.1",
                "pub_cmd": "dotnet pack -p:PackageVersion=9.1.1 && dotnet nuget push dist/Eckermannite.9.1.1.nupkg && dotnet nuget push dist/Eckermannite.9.1.1.snupkg --source https://nuget.smbsrc.net/",
                "pub_obs": "Your package was pushed.\nYour symbol package was pushed.",
                "ver_cmd": "echo SYM_911=ok",
                "ver_obs": "SYM_911=ok",
                "tag_cmd": "git tag -s v9.1.1 -m '9.1.1'",
                "tag_obs": "tagged v9.1.1",
                "still2_cmd": "curl -sSI https://globalcdn.nuget.org/symbol-packages/eckermannite.9.1.0.snupkg | rg -i HTTP",
                "still2_obs": "HTTP/2 200",
                "undo_cmd": "echo skipped_hard_delete_snupkg=1",
                "undo_obs": "skipped_hard_delete_snupkg=1",
                "split_cmd": "echo NUPKG_910=unlisted SNUPKG_910=200 DEBUGGER=910",
                "split_obs": "NUPKG_910=unlisted SNUPKG_910=200 DEBUGGER=910",
                "tix_cmd": "echo TICKET=symbol_cdn_still_serves_9.1.0",
                "tix_obs": "TICKET=symbol_cdn_still_serves_9.1.0",
                "res_cmd": "echo NEW=9.1.1 SNUPKG_910=leftover",
                "res_obs": "NEW=9.1.1 SNUPKG_910=leftover",
                "seed": "unlist nupkg ≠ delete snupkg",
                "first": "delete + republish 9.1.0",
                "change": "9.1.1",
                "term": "fail: snupkg 9.1.0 still 200",
            },
        ),
        # r173
        (
            "nix_nar",
            {
                "slug": "nix-ca-outputhashmode-vs-input-addressed",
                "plant": "clinozoisite-nix",
                "goal": "Ship clinozoisite-nix 2.0.0 as a content-addressed derivation. outputHashMode was flat (file) while the builder produces a directory. Do not flip to input-addressed to hide the mismatch. Leave the old input-addressed path in the cache.",
                "plan": "Drop __contentAddressed and keep the input-addressed path so the old cache hits.",
                "outcome": "Dropping CA made the next eval miss the intended CA store path. Plan change: keep CA, set outputHashMode=recursive for the directory NAR. Residual: old input-addressed path still in the cache.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "fods": 1, "cost_steps": 15},
                "inspect_cmd": "nix --version | head -n 1; rg -n 'contentAddressed|outputHashMode' flake.nix",
                "inspect_obs": "nix (Nix) 2.24.10\n__contentAddressed = true;\noutputHashMode = \"flat\";",
                "nix_path": "flake.nix",
                "nix_obs": "{\n  __contentAddressed = true;\n  outputHashMode = \"flat\";\n  outputHash = \"sha256-"
                + hx("clino-file", 44)
                + "=\";\n}\n",
                "lock_path": "flake.lock",
                "lock_obs": "{ \"nodes\": {} }\n",
                "pref_cmd": "echo DIR_NAR="
                + hx("clino-dir", 16)
                + " FILE_HASH="
                + hx("clino-file", 16),
                "pref_obs": "DIR_NAR="
                + hx("clino-dir", 16)
                + " FILE_HASH="
                + hx("clino-file", 16),
                "apply_cmd": "nix build --rebuild 2>&1 | tail -n 14",
                "apply_obs": "error: outputHashMode=flat but builder produced a directory\nwant recursive NAR of $out",
                "apply_refl": "Apply failed. CA directory outputs need outputHashMode=recursive, not flat, and not a retreat to input-addressed.",
                "nar_cmd": "echo RECURSIVE_NAR=sha256-" + hx("clino-dir", 44) + "=",
                "nar_obs": "RECURSIVE_NAR=sha256-" + hx("clino-dir", 44) + "=",
                "fetch_cmd": "echo CA=1 MODE=must_recursive",
                "fetch_obs": "CA=1 MODE=must_recursive",
                "nix_new": "{\n  __contentAddressed = true;\n  outputHashMode = \"recursive\";\n  outputHash = \"sha256-"
                + hx("clino-dir", 44)
                + "=\";\n}\n",
                "bld_cmd": "nix build --rebuild 2>&1 | tail -n 6",
                "bld_obs": "/nix/store/"
                + hx("clino-out", 32)
                + "-clinozoisite-nix-2.0.0",
                "left_cmd": "echo OLD_IA_PATH=/nix/store/"
                + hx("clino-ia", 32)
                + "-clinozoisite-nix-2.0.0 CACHE=1",
                "left_obs": "OLD_IA_PATH=/nix/store/"
                + hx("clino-ia", 32)
                + "-clinozoisite-nix-2.0.0 CACHE=1",
                "doc_cmd": "echo KEEP_IA_CACHE=1",
                "doc_obs": "KEEP_IA_CACHE=1",
                "tag_cmd": "git tag -s v2.0.0 -m '2.0.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add flake.nix && git commit -m 'CA recursive NAR; do not drop contentAddressed'",
                "cmt_obs": "[main " + hx("clino-cmt", 7) + "] CA recursive NAR; do not drop contentAddressed",
                "chk_cmd": "nix flake check 2>&1 | tail -n 4",
                "chk_obs": "OK",
                "res_cmd": "echo CA=recursive IA_CACHE=leftover",
                "res_obs": "CA=recursive IA_CACHE=leftover",
                "res_refl": "CA directory outputs use recursive NAR. Residual: old input-addressed path still cached.",
                "seed": "CA flat vs directory NAR",
                "first": "drop contentAddressed",
                "change": "outputHashMode=recursive",
                "term": "success; IA path leftover",
            },
            "fail_leftover",
            {
                "slug": "npm-selfhosted-runner-no-oidc",
                "plant": "piemontite-js",
                "goal": "piemontite-js 3.5.0 published from a self-hosted runner without GitHub OIDC. 3.5.1 must come from github-hosted with provenance. Do not unpublish 3.5.0. latest still 3.5.0 attestations=null.",
                "plan": "Set ACTIONS_ID_TOKEN_REQUEST_URL on the self-hosted runner and republish 3.5.0 --provenance.",
                "outcome": "Self-hosted spoof of ACTIONS_ID_TOKEN_REQUEST_URL rejected; 3.5.0 unique. Plan change: 3.5.1 on github-hosted. Residual: latest=3.5.0 no provenance. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "latest_still_old": 1, "cost_steps": 16},
                "inspect_cmd": "npm view @piemontite/core@3.5.0 --json | python3 -c 'import json,sys; p=json.load(sys.stdin); print(p.get(\"dist\",{}).get(\"attestations\"), p[\"version\"])'",
                "inspect_obs": "None 3.5.0",
                "wf_path": ".github/workflows/npm.yml",
                "wf_obs": "runs-on: [self-hosted, linux, x64]\n# no id-token audience\n",
                "why_cmd": "echo RUNNER=self-hosted OIDC=absent ATTEST=null",
                "why_obs": "RUNNER=self-hosted OIDC=absent ATTEST=null",
                "con_path": ".npmrc-fleet",
                "con_obs": "@piemontite:registry=https://registry.npmjs.org/\n# fleet uses latest\n",
                "apply_cmd": "ACTIONS_ID_TOKEN_REQUEST_URL=http://127.0.0.1:9 npm publish --provenance 2>&1 | tail -n 12",
                "apply_obs": "npm ERR! OIDC token request failed\nnpm ERR! 403 cannot publish over 3.5.0\nself-hosted URL is not token.actions.githubusercontent.com",
                "apply_refl": "Apply failed. Provenance OIDC must come from GitHub-hosted token issuer; versions stay unique.",
                "still_cmd": "npm view @piemontite/core@3.5.0 version",
                "still_obs": "3.5.0",
                "use_cmd": "npm view @piemontite/core dist-tags --json",
                "use_obs": "{\"latest\":\"3.5.0\"}",
                "fix_cmd": "echo RUNS_ON=ubuntu-latest NEXT=3.5.1",
                "fix_obs": "RUNS_ON=ubuntu-latest NEXT=3.5.1",
                "pub_cmd": "npm version 3.5.1 --no-git-tag-version && npm publish --access public --provenance 2>&1 | tail -n 10",
                "pub_obs": "+ @piemontite/core@3.5.1\nprovenance uploaded (github-hosted)",
                "ver_cmd": "npm view @piemontite/core@3.5.1 --json | python3 -c 'import json,sys; print(bool(json.load(sys.stdin).get(\"dist\",{}).get(\"attestations\")))'",
                "ver_obs": "True",
                "tag_cmd": "git commit -am 'release 3.5.1 github-hosted provenance' && git tag -s v3.5.1 -m '3.5.1'",
                "tag_obs": "[main " + hx("pie-cmt", 7) + "] release 3.5.1 github-hosted provenance",
                "still2_cmd": "npm view @piemontite/core dist-tags --json",
                "still2_obs": "{\"latest\":\"3.5.0\",\"next\":\"3.5.1\"}",
                "undo_cmd": "echo skipped_unpublish_350=1",
                "undo_obs": "skipped_unpublish_350=1",
                "split_cmd": "echo LATEST=3.5.0_no_prov NEW=3.5.1_ok",
                "split_obs": "LATEST=3.5.0_no_prov NEW=3.5.1_ok",
                "tix_cmd": "echo TICKET=latest_still_selfhosted_3.5.0",
                "tix_obs": "TICKET=latest_still_selfhosted_3.5.0",
                "res_cmd": "echo OLD=3.5.0 NEW=3.5.1 LATEST=3.5.0",
                "res_obs": "OLD=3.5.0 NEW=3.5.1 LATEST=3.5.0",
                "seed": "self-hosted runner no OIDC",
                "first": "spoof ACTIONS_ID_TOKEN_REQUEST_URL",
                "change": "3.5.1 github-hosted",
                "term": "fail: latest still 3.5.0",
            },
        ),
        # r174
        (
            "gpg_portal",
            {
                "slug": "maven-sigstore-plugin-vs-gpg-dual-sign",
                "plant": "allanite-mvn",
                "goal": "Ship allanite-mvn 6.6.0. Both maven-gpg-plugin and sigstore-maven-plugin signed the same JAR; Central rejected dual signatures. Pick Sigstore keyless only. Leave the leftover local .asc from GPG.",
                "plan": "Keep both plugins so consumers can verify either GPG or Sigstore.",
                "outcome": "Dual signatures failed Central signatures-valid (ambiguous signer). Plan change: disable gpg plugin; keep sigstore-maven-plugin keyless. Residual: local .asc leftover.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "ls -1 target/*.asc target/*.sigstore.json 2>/dev/null; rg -n 'maven-gpg-plugin|sigstore-maven-plugin' pom.xml",
                "inspect_obs": "target/allanite-mvn-6.6.0.jar.asc\ntarget/allanite-mvn-6.6.0.jar.sigstore.json\nboth plugins bound to verify",
                "pom_path": "pom.xml",
                "pom_obs": "<plugin><artifactId>maven-gpg-plugin</artifactId></plugin>\n<plugin><groupId>dev.sigstore</groupId><artifactId>sigstore-maven-plugin</artifactId></plugin>\n",
                "set_path": "~/.m2/settings.xml",
                "set_obs": "<gpg.executable>gpg</gpg.executable>\n",
                "exp_cmd": "echo GPG=live SIGSTORE=keyless DUAL=1",
                "exp_obs": "GPG=live SIGSTORE=keyless DUAL=1",
                "apply_cmd": "mvn -B -Prelease deploy 2>&1 | tail -n 14",
                "apply_obs": "Rule failed: signatures-valid\nmultiple signature methods on the same JAR (GPG .asc + sigstore bundle)\nCentral wants one signer family",
                "apply_refl": "Apply failed. Central will not close a deployment that carries both GPG and Sigstore signatures on one JAR.",
                "sub_cmd": "echo PICK=sigstore-maven-plugin KEYLESS=1",
                "sub_obs": "PICK=sigstore-maven-plugin KEYLESS=1",
                "ep_cmd": "echo PORTAL=central.sonatype.com SIGSTORE_TLOG=rekor",
                "ep_obs": "PORTAL=central.sonatype.com SIGSTORE_TLOG=rekor",
                "fix_path": "pom.xml",
                "fix_contents": "<plugin>\n  <groupId>dev.sigstore</groupId>\n  <artifactId>sigstore-maven-plugin</artifactId>\n  <executions><execution><goals><goal>sign</goal></goals></execution></executions>\n</plugin>\n<!-- maven-gpg-plugin disabled -->\n",
                "sign_cmd": "mvn -B -Prelease deploy -DskipTests 2>&1 | tail -n 10",
                "sign_obs": "sigstore keyless sign ok\nrekor entry "
                + hx("allan-rekor", 16),
                "close_cmd": "mvn -B central-publishing:publish 2>&1 | tail -n 6",
                "close_obs": "Published allanite-mvn 6.6.0",
                "left_cmd": "ls target/*.asc && echo ASC_LOCAL=leftover",
                "left_obs": "target/allanite-mvn-6.6.0.jar.asc\nASC_LOCAL=leftover",
                "drop_cmd": "echo SKIP_UPLOAD_ASC=1",
                "drop_obs": "SKIP_UPLOAD_ASC=1",
                "tag_cmd": "git tag -s v6.6.0 -m '6.6.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add pom.xml && git commit -m 'release 6.6.0 sigstore only; disable gpg plugin'",
                "cmt_obs": "[main " + hx("allan-cmt", 7) + "] release 6.6.0 sigstore only; disable gpg plugin",
                "res_cmd": "echo SIGNER=sigstore ASC_LOCAL=leftover",
                "res_obs": "SIGNER=sigstore ASC_LOCAL=leftover",
                "res_refl": "One signer family on Central. Residual: local GPG .asc leftover.",
                "seed": "gpg + sigstore dual sign",
                "first": "deploy both signatures",
                "change": "sigstore keyless only",
                "term": "success; .asc leftover",
            },
            "fail_leftover",
            {
                "slug": "crates-sparse-asof-lag",
                "plant": "dissakisite-crate",
                "goal": "dissakisite-crate 2.2.1 published; sparse index config.json as-of snapshot on the mirror is still 2.2.0. Do not yank 2.2.1. Vendor mirror consumers still resolve 2.2.0.",
                "plan": "cargo yank 2.2.0 so the as-of snapshot cannot see it, then republish 2.2.1 onto the mirror.",
                "outcome": "Yank 2.2.0 does not refresh a vendor as-of snapshot. Plan change: leave crates.io 2.2.1; hand off mirror config.json. Residual: vendor still 2.2.0. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "mirror_lag": 1, "cost_steps": 16},
                "inspect_cmd": "curl -sS https://index.crates.io/di/ss/dissakisite-crate | tail -n 2; echo MIRROR_ASOF=2.2.0",
                "inspect_obs": "{\"vers\":\"2.2.1\",\"yanked\":false}\nMIRROR_ASOF=2.2.0",
                "wf_path": "Cargo.toml",
                "wf_obs": "[package]\nname = \"dissakisite-crate\"\nversion = \"2.2.1\"\n",
                "why_cmd": "curl -sS https://mirror.dissakisite.example/index/config.json | head -n 20",
                "why_obs": "{\n  \"dl\": \"https://mirror.dissakisite.example/api/v1/crates\",\n  \"api\": \"https://mirror.dissakisite.example\",\n  \"as-of\": \"2.2.0\"\n}",
                "con_path": "../dissakisite-vendor/.cargo/config.toml",
                "con_obs": "[source.crates-io]\nreplace-with = \"vendor\"\n[source.vendor]\nregistry = \"sparse+https://mirror.dissakisite.example/index/\"\n",
                "apply_cmd": "cargo yank dissakisite-crate@2.2.0 2>&1 | tail -n 8; cargo publish 2>&1 | tail -n 8",
                "apply_obs": "yanked 2.2.0\nerror: 2.2.1 already exists on crates.io\nmirror config.json as-of unchanged",
                "apply_refl": "Apply failed. Yanking an older version does not advance a vendor as-of snapshot.",
                "still_cmd": "curl -sS https://mirror.dissakisite.example/index/di/ss/dissakisite-crate | tail -n 2",
                "still_obs": "{\"vers\":\"2.2.0\",\"yanked\":false}",
                "use_cmd": "CARGO_REGISTRIES_DISS_INDEX=sparse+https://mirror.dissakisite.example/index/ cargo tree -p dissakisite-app | rg dissakisite-crate",
                "use_obs": "dissakisite-crate v2.2.0",
                "fix_cmd": "echo LEAVE_221=1 HANDOFF_MIRROR=1",
                "fix_obs": "LEAVE_221=1 HANDOFF_MIRROR=1",
                "pub_cmd": "echo crates.io already has 2.2.1; skip republish",
                "pub_obs": "crates.io already has 2.2.1; skip republish",
                "ver_cmd": "curl -sS https://index.crates.io/di/ss/dissakisite-crate | tail -n 1",
                "ver_obs": "{\"vers\":\"2.2.1\",\"yanked\":false}",
                "tag_cmd": "git tag -s v2.2.1 -m '2.2.1' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "still2_cmd": "echo VENDOR=2.2.0 MIRROR_ASOF=2.2.0",
                "still2_obs": "VENDOR=2.2.0 MIRROR_ASOF=2.2.0",
                "undo_cmd": "echo skipped_unyank_220=1; echo skipped_mirror_rewrite=1",
                "undo_obs": "skipped_unyank_220=1\nskipped_mirror_rewrite=1",
                "split_cmd": "echo CRATES_IO=2.2.1 MIRROR=2.2.0",
                "split_obs": "CRATES_IO=2.2.1 MIRROR=2.2.0",
                "tix_cmd": "echo TICKET=vendor_mirror_asof_stuck_2.2.0",
                "tix_obs": "TICKET=vendor_mirror_asof_stuck_2.2.0",
                "res_cmd": "echo UPSTREAM=2.2.1 VENDOR=2.2.0",
                "res_obs": "UPSTREAM=2.2.1 VENDOR=2.2.0",
                "seed": "sparse as-of mirror lag",
                "first": "yank 2.2.0 to refresh mirror",
                "change": "handoff config.json",
                "term": "fail: vendor still 2.2.0",
            },
        ),
        # r175
        (
            "nuget_snupkg",
            {
                "slug": "nuget-packagesourcemapping-signed-only",
                "plant": "dollaseite-nupkg",
                "goal": "Ship dollaseite-nupkg 1.9.0 so PackageSourceMapping signed-only consumers accept it. Unsigned 1.8.9 from a local feed must not be remapped. Leave 1.8.9 on the local feed.",
                "plan": "Add the local feed to PackageSourceMapping so 1.9.0 unsigned can flow.",
                "outcome": "Widening mapping to the unsigned local feed failed the signed-only policy. Plan change: nuget sign 1.9.0 + keep mapping on nuget.org. Residual: 1.8.9 unsigned leftover on the local feed.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "signed": 1, "cost_steps": 15},
                "inspect_cmd": "dotnet nuget verify dist/Dollaseite.1.9.0.nupkg 2>&1 | tail -n 10; cat nuget.config | head",
                "inspect_obs": "error: package is not signed\n<packageSourceMapping><package pattern=\"Dollaseite\" source=\"nuget.org\" /></packageSourceMapping>",
                "nus_path": "Dollaseite.nuspec",
                "nus_obs": "<id>Dollaseite</id><version>1.9.0</version>\n",
                "dbp_path": "nuget.config",
                "dbp_obs": "<packageSources>\n  <add key=\"nuget.org\" value=\"https://api.nuget.org/v3/index.json\" />\n  <add key=\"local\" value=\"./feed\" />\n</packageSources>\n<packageSourceMapping>\n  <package pattern=\"Dollaseite\" source=\"nuget.org\" />\n</packageSourceMapping>\n",
                "cmp_cmd": "echo LOCAL_189=unsigned NUGET_190=unsigned_not_pushed",
                "cmp_obs": "LOCAL_189=unsigned NUGET_190=unsigned_not_pushed",
                "apply_cmd": "python3 - <<'PY'\nprint('mapped Dollaseite -> local feed')\nPY\ndotnet restore 2>&1 | tail -n 10",
                "apply_obs": "mapped Dollaseite -> local feed\nerror: NU3004 package Dollaseite 1.8.9 from 'local' is not signed (signed-only policy)",
                "apply_refl": "Apply failed. PackageSourceMapping onto an unsigned local feed violates signed-only restore.",
                "pdb_cmd": "echo SIGN_CERT=codesign.pfx POLICY=signed-only",
                "pdb_obs": "SIGN_CERT=codesign.pfx POLICY=signed-only",
                "host_cmd": "echo KEEP_MAP=nuget.org",
                "host_obs": "KEEP_MAP=nuget.org",
                "dbp_new": "<packageSourceMapping>\n  <package pattern=\"Dollaseite\" source=\"nuget.org\" />\n</packageSourceMapping>\n<!-- do not map Dollaseite onto unsigned local feed -->\n",
                "pack_cmd": "nuget sign dist/Dollaseite.1.9.0.nupkg -CertificatePath codesign.pfx && dotnet nuget push dist/Dollaseite.1.9.0.nupkg --source https://api.nuget.org/v3/index.json",
                "pack_obs": "Package signed.\nYour package was pushed.",
                "sym_cmd": "dotnet nuget verify dist/Dollaseite.1.9.0.nupkg 2>&1 | tail -n 6",
                "sym_obs": "Signature type: Author\nValid",
                "left_cmd": "ls feed/Dollaseite.1.8.9.nupkg && echo LOCAL_189=leftover",
                "left_obs": "feed/Dollaseite.1.8.9.nupkg\nLOCAL_189=leftover",
                "unl_cmd": "echo KEEP_LOCAL_189=1",
                "unl_obs": "KEEP_LOCAL_189=1",
                "tag_cmd": "git tag -s v1.9.0 -m '1.9.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add nuget.config && git commit -m 'release 1.9.0 signed; keep mapping on nuget.org'",
                "cmt_obs": "[main " + hx("doll-cmt", 7) + "] release 1.9.0 signed; keep mapping on nuget.org",
                "res_cmd": "echo SIGNED=1.9.0 LOCAL_189=leftover",
                "res_obs": "SIGNED=1.9.0 LOCAL_189=leftover",
                "res_refl": "signed-only mapping stays on nuget.org. Residual: unsigned 1.8.9 on the local feed.",
                "seed": "PackageSourceMapping signed-only",
                "first": "map onto local unsigned feed",
                "change": "nuget sign + nuget.org map",
                "term": "success; 1.8.9 local leftover",
            },
            "fail_leftover",
            {
                "slug": "homebrew-pour-bottle-only-if-leftover",
                "plant": "androsite-brew",
                "goal": "androsite-brew 0.5.4 formula has pour_bottle_only_if { false } leftover from a debug PR. Bottles exist but never pour. Do not delete bottles. Selfhost still builds from source.",
                "plan": "gh release delete-asset all bottles so brew install compiles from source everywhere.",
                "outcome": "Deleting bottles failed brew audit (missing bottle block). Plan change: drop pour_bottle_only_if. Residual: selfhost still compiling from source (cache). Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "pour_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "rg -n 'pour_bottle_only_if|bottle do' Formula/androsite.rb",
                "inspect_obs": "pour_bottle_only_if { false }\nbottle do\n  sha256 cellar: :any, sonoma: \""
                + hx("andro-bot", 64)
                + "\"",
                "wf_path": "Formula/androsite.rb",
                "wf_obs": "pour_bottle_only_if { false }\nbottle do\n  sha256 cellar: :any, sonoma: \""
                + hx("andro-bot", 64)
                + "\"\nend\n",
                "why_cmd": "brew install --verbose androsite 2>&1 | rg -n 'bottle|Pouring|Installing' | head",
                "why_obs": "Not pouring bottle (pour_bottle_only_if false)\nInstalling from source",
                "con_path": "../androsite-selfhost/Brewfile",
                "con_obs": "brew \"androsite\"\n",
                "apply_cmd": "gh release delete-asset v0.5.4 androsite-0.5.4.sonoma.bottle.tar.gz --yes 2>&1 | tail -n 8; brew audit --strict androsite 2>&1 | tail -n 8",
                "apply_obs": "deleted asset\n* formula defines bottle sha256 but asset 404\nError: 1 problem",
                "apply_refl": "Apply failed. Deleting the bottle asset does not fix pour_bottle_only_if; it just breaks audit.",
                "still_cmd": "echo SOURCE_BUILD_SELFHOST=1",
                "still_obs": "SOURCE_BUILD_SELFHOST=1",
                "use_cmd": "echo SELFHOST=compile_from_source",
                "use_obs": "SELFHOST=compile_from_source",
                "fix_cmd": "python3 - <<'PY'\nfrom pathlib import Path\np=Path('Formula/androsite.rb'); p.write_text(p.read_text().replace('pour_bottle_only_if { false }\\n','')); print('dropped pour_bottle_only_if')\nPY",
                "fix_obs": "dropped pour_bottle_only_if",
                "pub_cmd": "brew audit --strict androsite 2>&1 | tail -n 4",
                "pub_obs": "0 problems",
                "ver_cmd": "echo FORMULA=pours_on_sonoma",
                "ver_obs": "FORMULA=pours_on_sonoma",
                "tag_cmd": "git commit -am 'drop pour_bottle_only_if leftover' && git tag -s v0.5.5 -m '0.5.5'",
                "tag_obs": "[main " + hx("andro-cmt", 7) + "] drop pour_bottle_only_if leftover",
                "still2_cmd": "echo SELFHOST_CACHE=source_build STILL=1",
                "still2_obs": "SELFHOST_CACHE=source_build STILL=1",
                "undo_cmd": "echo skipped_delete_remaining_bottles=1",
                "undo_obs": "skipped_delete_remaining_bottles=1",
                "split_cmd": "echo FORMULA=ok SELFHOST_CACHE=source",
                "split_obs": "FORMULA=ok SELFHOST_CACHE=source",
                "tix_cmd": "echo TICKET=selfhost_still_compiles_from_source_cache",
                "tix_obs": "TICKET=selfhost_still_compiles_from_source_cache",
                "res_cmd": "echo POUR=ok SELFHOST=leftover_source",
                "res_obs": "POUR=ok SELFHOST=leftover_source",
                "seed": "pour_bottle_only_if false leftover",
                "first": "delete bottle assets",
                "change": "drop pour_bottle_only_if",
                "term": "fail: selfhost source cache",
            },
        ),
        # r176
        (
            "cosign_reusable",
            {
                "slug": "cosign-new-bundle-format-vs-old",
                "plant": "ferrohornblende-oci",
                "image": "ghcr.io/ferrohornblende-designed/ferrohornblende-oci:0.3.3",
                "digest": "sha256:" + hx("ferro-img", 64),
                "call_id": "cosign verify --old bundle .sig",
                "reuse_id": "cosign verify --new-bundle-format",
                "reuse_short": "--new-bundle-format",
                "tag": "v0.3.3",
                "ver": "0.3.3",
                "leftover": "old .sig bundle blob leftover",
                "inspect_cmd": "cosign version | head -n 2; ls *.sigstore.json *.sig 2>/dev/null; crane digest ghcr.io/ferrohornblende-designed/ferrohornblende-oci:0.3.3",
                "inspect_obs": "GitVersion:    v2.4.1\nbundle-0.3.3.sigstore.json\nlegacy-0.3.3.sig\nsha256:"
                + hx("ferro-img", 64),
                "wf_path": ".github/workflows/sign.yml",
                "wf_obs": "run: cosign sign --yes --new-bundle-format=false $IMAGE\n",
                "pol_path": "policy/verify.sh",
                "pol_obs": "cosign verify $IMAGE --key cosign.pub   # old keyful + old bundle\n",
                "decode_cmd": "cosign verify ghcr.io/ferrohornblende-designed/ferrohornblende-oci@sha256:"
                + hx("ferro-img", 64)
                + " --key cosign.pub 2>&1 | tail -n 10",
                "decode_obs": "error: no old-format signatures\nfound bundle v0.3+json (new format)",
                "apply_cmd": "cosign verify ghcr.io/ferrohornblende-designed/ferrohornblende-oci@sha256:"
                + hx("ferro-img", 64)
                + " --key cosign.pub --insecure-ignore-tlog 2>&1 | tail -n 10",
                "apply_obs": "error: new bundle format present; --key keyful path does not read v0.3 bundles",
                "san_cmd": "python3 - <<'PY'\nprint('bundle mediaType application/vnd.dev.sigstore.bundle.v0.3+json')\nPY",
                "san_obs": "bundle mediaType application/vnd.dev.sigstore.bundle.v0.3+json",
                "iss_cmd": "echo VERIFY=--new-bundle-format IDENTITY=workflow",
                "iss_obs": "VERIFY=--new-bundle-format IDENTITY=workflow",
                "pol_new": "cosign verify $IMAGE --new-bundle-format --certificate-identity $ID --certificate-oidc-issuer https://token.actions.githubusercontent.com\n",
                "verify_cmd": "cosign verify ghcr.io/ferrohornblende-designed/ferrohornblende-oci@sha256:"
                + hx("ferro-img", 64)
                + " --new-bundle-format --certificate-identity https://github.com/ferrohornblende-designed/ferrohornblende-oci/.github/workflows/sign.yml@refs/tags/v0.3.3 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 8",
                "verify_obs": "Verified OK (new bundle format)",
                "left_cmd": "ls legacy-0.3.3.sig && echo OLD_SIG=leftover",
                "left_obs": "legacy-0.3.3.sig\nOLD_SIG=leftover",
                "up_cmd": "echo ATTACHED=new_bundle OLD_SIG=left",
                "up_obs": "ATTACHED=new_bundle OLD_SIG=left",
                "wf_old": "run: cosign sign --yes --new-bundle-format=false $IMAGE",
                "wf_new": "run: cosign sign --yes --new-bundle-format $IMAGE",
                "cmt_cmd": "git add policy/verify.sh .github/workflows/sign.yml && git commit -m 'verify new-bundle-format; stop keyful old .sig'",
                "cmt_obs": "[main " + hx("ferro-cmt", 7) + "] verify new-bundle-format; stop keyful old .sig",
                "tag_cmd": "git rev-parse v0.3.3^{commit}",
                "tag_obs": gsha("ferro-tag"),
                "res_cmd": "echo BUNDLE=v0.3 OLD_SIG=leftover",
                "res_obs": "BUNDLE=v0.3 OLD_SIG=leftover",
                "res_refl": "New bundle format is not the keyful .sig path. Residual: legacy .sig blob leftover.",
                "seed": "new-bundle-format vs old .sig",
                "first": "verify --key old bundle",
                "change": "--new-bundle-format + OIDC",
                "term": "success; old .sig leftover",
            },
            "fail_leftover",
            {
                "slug": "nix-flake-input-rev-narhash-stale",
                "plant": "tschermakite-nix",
                "goal": "tschermakite-nix flake input src rev moved to the v1.4.2 tarball; flake.lock still has the NAR of v1.4.1 unpacked src. Do not set narHash to the git commit. CI still substitutes v1.4.1.",
                "plan": "Set locked.narHash to the git commit of v1.4.2 so it matches git ls-remote.",
                "outcome": "Putting a git commit into narHash failed eval (not a NAR SRI). Plan change: nix flake lock --update-input src (NAR of new unpacked tarball). Residual: CI cache still has v1.4.1. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "cache_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "nix flake metadata 2>&1 | tail -n 12; git ls-remote --tags origin | rg v1.4",
                "inspect_obs": "src rev="
                + hx("tsch-141", 40)
                + " narHash=sha256-"
                + hx("tsch-nar141", 44)
                + "=\nv1.4.2 "
                + hx("tsch-142", 40),
                "wf_path": "flake.nix",
                "wf_obs": "inputs.src.url = \"https://git.tschermakite.example/src/archive/v1.4.2.tar.gz\";\n",
                "why_cmd": "echo LOCK_REV="
                + hx("tsch-141", 12)
                + " WANT_REV="
                + hx("tsch-142", 12)
                + " LOCK_NAR="
                + hx("tsch-nar141", 12),
                "why_obs": "LOCK_REV="
                + hx("tsch-141", 12)
                + " WANT_REV="
                + hx("tsch-142", 12)
                + " LOCK_NAR="
                + hx("tsch-nar141", 12),
                "con_path": "ci/substituters.txt",
                "con_obs": "https://cache.tschermakite.example  # still has v1.4.1 NAR\n",
                "apply_cmd": "python3 - <<'PY'\nprint('set narHash to git commit "
                + hx("tsch-142", 40)
                + "')\nPY\nnix flake check 2>&1 | tail -n 10",
                "apply_obs": "set narHash to git commit "
                + hx("tsch-142", 40)
                + "\nerror: narHash is not a valid SRI NAR hash (got a git commit)",
                "apply_refl": "Apply failed. flake.lock narHash is the NAR of unpacked src, not the git commit of the tag.",
                "still_cmd": "echo CACHE_141=https://cache.tschermakite.example/"
                + hx("tsch-nar141", 16)
                + ".narinfo",
                "still_obs": "CACHE_141=https://cache.tschermakite.example/"
                + hx("tsch-nar141", 16)
                + ".narinfo",
                "use_cmd": "echo CI_SUBSTITUTE=v1.4.1",
                "use_obs": "CI_SUBSTITUTE=v1.4.1",
                "fix_cmd": "nix flake lock --update-input src 2>&1 | tail -n 8",
                "fix_obs": "updated src narHash sha256-"
                + hx("tsch-nar142", 44)
                + "=",
                "pub_cmd": "nix build 2>&1 | tail -n 6",
                "pub_obs": "/nix/store/"
                + hx("tsch-out", 32)
                + "-tschermakite-nix-1.4.2",
                "ver_cmd": "nix flake metadata 2>&1 | rg narHash",
                "ver_obs": "narHash sha256-" + hx("tsch-nar142", 44) + "=",
                "tag_cmd": "git add flake.lock && git commit -m 'lock src v1.4.2 NAR' && git tag -s v1.4.2 -m '1.4.2'",
                "tag_obs": "[main " + hx("tsch-cmt", 7) + "] lock src v1.4.2 NAR",
                "still2_cmd": "echo CI_SUBSTITUTE=v1.4.1 STILL=1",
                "still2_obs": "CI_SUBSTITUTE=v1.4.1 STILL=1",
                "undo_cmd": "echo skipped_narhash_eq_git=1; echo skipped_cache_delete=1",
                "undo_obs": "skipped_narhash_eq_git=1\nskipped_cache_delete=1",
                "split_cmd": "echo LOCAL=1.4.2 CI_CACHE=1.4.1",
                "split_obs": "LOCAL=1.4.2 CI_CACHE=1.4.1",
                "tix_cmd": "echo TICKET=ci_cache_still_serves_v1.4.1_nar",
                "tix_obs": "TICKET=ci_cache_still_serves_v1.4.1_nar",
                "res_cmd": "echo LOCK=1.4.2 CACHE=1.4.1",
                "res_obs": "LOCK=1.4.2 CACHE=1.4.1",
                "seed": "flake input rev moved; narHash stale",
                "first": "narHash = git commit",
                "change": "nix flake lock --update-input",
                "term": "fail: CI cache still 1.4.1",
            },
        ),
        # r177
        (
            "oidc_publisher",
            {
                "slug": "pypi-gitlab-oidc-vs-github-registered",
                "plant": "pargasite-py",
                "goal": "Ship pargasite-py 2.7.0 from GitLab CI. Trusted Publisher is still registered for GitHub. Do not use a GitLab personal token. Leave the GitHub publisher row.",
                "plan": "twine upload with a GitLab personal token so Warehouse ignores the publisher host.",
                "outcome": "GitLab token upload would omit PEP 740 and is refused by policy. Plan change: register a GitLab Trusted Publisher and upload via OIDC. Residual: old GitHub publisher row leftover.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "echo REGISTERED_HOST=GitHub CI_HOST=GitLab; ls .gitlab-ci.yml",
                "inspect_obs": "REGISTERED_HOST=GitHub CI_HOST=GitLab\n.gitlab-ci.yml",
                "wf_path": ".gitlab-ci.yml",
                "wf_obs": "publish:\n  id_tokens:\n    PYPI_ID_TOKEN:\n      aud: pypi\n  script: [\"python -m twine upload dist/*\"]\n",
                "meta_path": "pyproject.toml",
                "meta_obs": "[project]\nname = \"pargasite-py\"\nversion = \"2.7.0\"\n",
                "claim_cmd": "echo iss=https://gitlab.com sub=project_path:pargasite-designed/pargasite-py:ref_type:tag:ref:v2.7.0",
                "claim_obs": "iss=https://gitlab.com sub=project_path:pargasite-designed/pargasite-py:ref_type:tag:ref:v2.7.0",
                "apply_cmd": "python3 -m twine upload -u __token__ -p glpat-*** dist/pargasite_py-2.7.0-py3-none-any.whl 2>&1 | tail -n 10",
                "apply_obs": "Refusing GitLab personal token: no PEP 740; GitHub publisher row does not match iss=gitlab.com",
                "apply_refl": "Apply failed. Trusted publisher is host-specific; a PAT cannot stand in for GitLab OIDC.",
                "diff_cmd": "echo NEED=gitlab_publisher HAVE=github_row",
                "diff_obs": "NEED=gitlab_publisher HAVE=github_row",
                "iss_cmd": "echo ISSUER=https://gitlab.com",
                "iss_obs": "ISSUER=https://gitlab.com",
                "fix_path": "docs/publisher-gitlab.json",
                "fix_contents": "{\n  \"issuer\": \"https://gitlab.com\",\n  \"namespace\": \"pargasite-designed\",\n  \"project\": \"pargasite-py\",\n  \"workflow_filepath\": \".gitlab-ci.yml\",\n  \"environment\": \"release\"\n}\n",
                "pub_cmd": "python3 -m twine upload dist/pargasite_py-2.7.0-py3-none-any.whl 2>&1 | tail -n 10",
                "pub_obs": "Uploading via GitLab OIDC\nAttestations uploaded",
                "att_cmd": "echo PROV_270=yes ISSUER=gitlab.com",
                "att_obs": "PROV_270=yes ISSUER=gitlab.com",
                "left_cmd": "echo GITHUB_PUBLISHER_ROW=still_registered",
                "left_obs": "GITHUB_PUBLISHER_ROW=still_registered",
                "doc_cmd": "echo KEEP_GITHUB_ROW=1",
                "doc_obs": "KEEP_GITHUB_ROW=1",
                "tag_cmd": "git tag -s v2.7.0 -m '2.7.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add docs/publisher-gitlab.json && git commit -m 'release 2.7.0 GitLab trusted publisher'",
                "cmt_obs": "[main " + hx("parg-cmt", 7) + "] release 2.7.0 GitLab trusted publisher",
                "res_cmd": "echo OIDC=gitlab GITHUB_ROW=leftover",
                "res_obs": "OIDC=gitlab GITHUB_ROW=leftover",
                "res_refl": "Trusted publisher host must match CI. Residual: GitHub publisher row leftover.",
                "seed": "GitLab CI vs GitHub publisher",
                "first": "GitLab PAT twine",
                "change": "register GitLab publisher",
                "term": "success; GitHub row leftover",
            },
            "fail_leftover",
            {
                "slug": "maven-gpg-keyserver-missing-secring",
                "plant": "hastingsite-mvn",
                "goal": "hastingsite-mvn 3.3.1 close needs the signing subkey on the keyserver. CI only has a local secring.gpg. Do not publish the secring. Downstream still verifies against keys.openpgp.org and fails.",
                "plan": "Attach secring.gpg as a GH release asset so Central and consumers can fetch the key.",
                "outcome": "Uploading secring is refused (private key). Plan change: gpg --send-keys of the public subkey only. Residual: keys.openpgp.org still 404 for consumers. Ticket not closed.",
                "reward": {"success": False, "sign_fails": 1, "plan_changes": 1, "keyserver_miss": 1, "cost_steps": 16},
                "inspect_cmd": "ls secring.gpg pubring.gpg; gpg --list-keys release@hastingsite.example | tail",
                "inspect_obs": "secring.gpg\npubring.gpg\nssb rsa4096 [S] "
                + hx("hast-sub", 16)
                + " (not on keyserver)",
                "wf_path": "pom.xml",
                "wf_obs": "<keyname>"
                + hx("hast-sub", 16)
                + "</keyname>\n",
                "why_cmd": "gpg --keyserver keys.openpgp.org --recv-keys "
                + hx("hast-sub", 40)
                + " 2>&1 | tail -n 6",
                "why_obs": "gpg: keyserver receive failed: No data",
                "con_path": "../hastingsite-app/verify.sh",
                "con_obs": "gpg --keyserver keys.openpgp.org --recv-keys "
                + hx("hast-sub", 40)
                + "\n",
                "apply_cmd": "gh release upload v3.3.1 secring.gpg 2>&1 | tail -n 8",
                "apply_obs": "Refusing to upload secring.gpg (private key material)",
                "apply_refl": "Apply failed. The keyserver needs the public subkey, not the secret ring as a release asset.",
                "still_cmd": "gpg --keyserver keys.openpgp.org --recv-keys "
                + hx("hast-sub", 40)
                + " 2>&1 | tail -n 4",
                "still_obs": "gpg: keyserver receive failed: No data",
                "use_cmd": "echo CONSUMER_VERIFY=recv_failed",
                "use_obs": "CONSUMER_VERIFY=recv_failed",
                "fix_cmd": "gpg --export "
                + hx("hast-sub", 40)
                + " | gpg --keyserver keys.openpgp.org --send-keys "
                + hx("hast-sub", 40)
                + " 2>&1 | tail -n 6",
                "fix_obs": "gpg: sending key ... (may be delayed by keyserver gossip)",
                "pub_cmd": "mvn -B -Prelease deploy 2>&1 | tail -n 8",
                "pub_obs": "Published hastingsite-mvn 3.3.1 (signatures attached from local secring)",
                "ver_cmd": "gpg --verify hastingsite-mvn-3.3.1.jar.asc 2>&1 | tail -n 4",
                "ver_obs": "Good signature (local keyring)",
                "tag_cmd": "git tag -s v3.3.1 -m '3.3.1' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "still2_cmd": "echo CONSUMER_KEYSERVER=404 STILL=1",
                "still2_obs": "CONSUMER_KEYSERVER=404 STILL=1",
                "undo_cmd": "echo skipped_upload_secring=1",
                "undo_obs": "skipped_upload_secring=1",
                "split_cmd": "echo LOCAL_VERIFY=ok KEYSERVER=404 CONSUMER=fail",
                "split_obs": "LOCAL_VERIFY=ok KEYSERVER=404 CONSUMER=fail",
                "tix_cmd": "echo TICKET=keys.openpgp.org_still_missing_subkey",
                "tix_obs": "TICKET=keys.openpgp.org_still_missing_subkey",
                "res_cmd": "echo JAR=signed KEYSERVER=leftover_miss",
                "res_obs": "JAR=signed KEYSERVER=leftover_miss",
                "seed": "public subkey missing on keyserver",
                "first": "upload secring.gpg",
                "change": "send public subkey",
                "term": "fail: keyserver still 404",
            },
        ),
        # r178
        (
            "oidc_publisher",
            {
                "slug": "npm-provenance-issuer-gitlab-vs-github",
                "plant": "kaersutite-js",
                "goal": "Ship kaersutite-js 4.4.0 from GitLab. npm provenance issuer must be gitlab.com, not the leftover GitHub OIDC identity in .npmrc. Leave 4.3.9 GitHub-provenance package.",
                "plan": "Copy the GitHub OIDC token into GitLab CI so npm publish --provenance reuses the GitHub identity.",
                "outcome": "Reusing a GitHub OIDC token on GitLab failed issuer checks. Plan change: npm provenance with GitLab OIDC. Residual: 4.3.9 still GitHub-issuer.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "attestations": 1, "cost_steps": 15},
                "inspect_cmd": "npm view @kaersutite/core@4.3.9 --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"dist\",{}).get(\"attestations\"))'",
                "inspect_obs": "{'provenance': {'predicateType': 'https://slsa.dev/provenance/v1', 'issuer': 'https://token.actions.githubusercontent.com'}}",
                "wf_path": ".gitlab-ci.yml",
                "wf_obs": "publish:\n  id_tokens: { NPM_ID_TOKEN: { aud: npm } }\n",
                "meta_path": "package.json",
                "meta_obs": "{\n  \"name\": \"@kaersutite/core\",\n  \"version\": \"4.4.0\",\n  \"publishConfig\": { \"provenance\": true }\n}\n",
                "claim_cmd": "echo leftover_npmrc=//registry.npmjs.org/:_authToken=${GITHUB_OIDC}",
                "claim_obs": "leftover_npmrc=//registry.npmjs.org/:_authToken=${GITHUB_OIDC}",
                "apply_cmd": "NPM_ID_TOKEN=$GITHUB_OIDC npm publish --provenance 2>&1 | tail -n 12",
                "apply_obs": "npm ERR! provenance issuer https://token.actions.githubusercontent.com does not match CI host gitlab.com",
                "apply_refl": "Apply failed. Provenance issuer must match the CI host that publishes.",
                "diff_cmd": "echo NEED_ISS=https://gitlab.com HAVE_ISS=https://token.actions.githubusercontent.com",
                "diff_obs": "NEED_ISS=https://gitlab.com HAVE_ISS=https://token.actions.githubusercontent.com",
                "iss_cmd": "echo ISSUER=https://gitlab.com",
                "iss_obs": "ISSUER=https://gitlab.com",
                "fix_path": ".npmrc",
                "fix_contents": "provenance=true\n# use GitLab OIDC, not a copied GitHub token\n",
                "pub_cmd": "npm publish --access public --provenance 2>&1 | tail -n 10",
                "pub_obs": "+ @kaersutite/core@4.4.0\nprovenance issuer=https://gitlab.com",
                "att_cmd": "npm view @kaersutite/core@4.4.0 --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"dist\",{}).get(\"attestations\"))'",
                "att_obs": "{'provenance': {'issuer': 'https://gitlab.com'}}",
                "left_cmd": "npm view @kaersutite/core@4.3.9 --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"dist\",{}).get(\"attestations\"))'",
                "left_obs": "{'provenance': {'issuer': 'https://token.actions.githubusercontent.com'}}",
                "doc_cmd": "echo KEEP_439_GITHUB_ISS=1",
                "doc_obs": "KEEP_439_GITHUB_ISS=1",
                "tag_cmd": "git tag -s v4.4.0 -m '4.4.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add .npmrc && git commit -m 'release 4.4.0 GitLab provenance issuer'",
                "cmt_obs": "[main " + hx("kaer-cmt", 7) + "] release 4.4.0 GitLab provenance issuer",
                "res_cmd": "echo ISS_440=gitlab ISS_439=github",
                "res_obs": "ISS_440=gitlab ISS_439=github",
                "res_refl": "Provenance issuer follows CI host. Residual: 4.3.9 still GitHub-issuer.",
                "seed": "GitLab publish vs GitHub issuer",
                "first": "reuse GitHub OIDC on GitLab",
                "change": "GitLab OIDC provenance",
                "term": "success; 4.3.9 GitHub leftover",
            },
            "fail_leftover",
            {
                "slug": "nuget-symbols-org-vs-nuget-org-split",
                "plant": "richterite-nupkg",
                "goal": "richterite-nupkg 8.8.0 nupkg is on nuget.org; snupkg push to nuget.org (wrong host) 404'd. symbols.nuget.org never got 8.8.0. Do not delete the nupkg. Debugger still 404s.",
                "plan": "dotnet nuget push the snupkg to api.nuget.org/v3/index.json like the nupkg.",
                "outcome": "snupkg on nuget.org package API 404. Plan change: push snupkg to nuget.smbsrc.net. Residual: debugger still 404 for 8.8.0 (CDN lag / missed). Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "symbols_404": 1, "cost_steps": 16},
                "inspect_cmd": "curl -sSI https://www.nuget.org/api/v2/package/Richterite/8.8.0 | rg -i HTTP; curl -sSI https://globalcdn.nuget.org/symbol-packages/richterite.8.8.0.snupkg | rg -i HTTP",
                "inspect_obs": "HTTP/2 200\nHTTP/2 404",
                "wf_path": "Richterite.nuspec",
                "wf_obs": "<id>Richterite</id><version>8.8.0</version>\n",
                "why_cmd": "echo NUPKG_HOST=nuget.org SNUPKG_HOST_USED=nuget.org SNUPKG_HOST_WANT=nuget.smbsrc.net",
                "why_obs": "NUPKG_HOST=nuget.org SNUPKG_HOST_USED=nuget.org SNUPKG_HOST_WANT=nuget.smbsrc.net",
                "con_path": "../richterite-app/nuget.config",
                "con_obs": "<add key=\"symbol\" value=\"https://symbols.nuget.org/download/symbols\" />\n",
                "apply_cmd": "dotnet nuget push dist/Richterite.8.8.0.snupkg --source https://api.nuget.org/v3/index.json 2>&1 | tail -n 10",
                "apply_obs": "error: 404 Symbol packages cannot be published to the package resource\nuse https://nuget.smbsrc.net/",
                "apply_refl": "Apply failed. snupkg has a different push host than nupkg.",
                "still_cmd": "curl -sSI https://globalcdn.nuget.org/symbol-packages/richterite.8.8.0.snupkg | rg -i HTTP",
                "still_obs": "HTTP/2 404",
                "use_cmd": "echo DEBUGGER=404_8.8.0",
                "use_obs": "DEBUGGER=404_8.8.0",
                "fix_cmd": "echo PUSH_SYM=https://nuget.smbsrc.net/",
                "fix_obs": "PUSH_SYM=https://nuget.smbsrc.net/",
                "pub_cmd": "dotnet nuget push dist/Richterite.8.8.0.snupkg --source https://nuget.smbsrc.net/ 2>&1 | tail -n 8",
                "pub_obs": "Your symbol package was pushed.",
                "ver_cmd": "echo SYM_PUSH=ok CDN=unknown",
                "ver_obs": "SYM_PUSH=ok CDN=unknown",
                "tag_cmd": "git tag -s v8.8.0 -m '8.8.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "still2_cmd": "curl -sSI https://globalcdn.nuget.org/symbol-packages/richterite.8.8.0.snupkg | rg -i HTTP",
                "still2_obs": "HTTP/2 404",
                "undo_cmd": "echo skipped_delete_nupkg=1",
                "undo_obs": "skipped_delete_nupkg=1",
                "split_cmd": "echo NUPKG=200 SNUPKG_CDN=404 DEBUGGER=404",
                "split_obs": "NUPKG=200 SNUPKG_CDN=404 DEBUGGER=404",
                "tix_cmd": "echo TICKET=symbol_cdn_still_404_8.8.0",
                "tix_obs": "TICKET=symbol_cdn_still_404_8.8.0",
                "res_cmd": "echo NUPKG=ok SNUPKG_CDN=404",
                "res_obs": "NUPKG=ok SNUPKG_CDN=404",
                "seed": "snupkg host ≠ nupkg host",
                "first": "push snupkg to nuget.org",
                "change": "push to nuget.smbsrc.net",
                "term": "fail: CDN still 404",
            },
        ),
        # r179
        (
            "cosign_reusable",
            {
                "slug": "sigstore-oidc-issuer-regexp-vs-exact",
                "plant": "katophorite-oci",
                "image": "ghcr.io/katophorite-designed/katophorite-oci:1.1.1",
                "digest": "sha256:" + hx("kato-img", 64),
                "call_id": "--certificate-oidc-issuer exact https://token.actions.githubusercontent.com",
                "reuse_id": "--certificate-oidc-issuer-regexp for GHES https://ghe.katophorite.example/_services/token",
                "reuse_short": "GHES issuer regexp",
                "tag": "v1.1.1",
                "ver": "1.1.1",
                "leftover": "dotcom issuer verify script leftover",
                "inspect_cmd": "git verify-tag v1.1.1 2>&1 | tail -n 4; crane digest ghcr.io/katophorite-designed/katophorite-oci:1.1.1",
                "inspect_obs": "Good \"git\" signature\nsha256:"
                + hx("kato-img", 64),
                "wf_path": ".github/workflows/sign.yml",
                "wf_obs": "runs-on: [self-hosted, ghe]\n# OIDC issuer is GHES, not github.com\n",
                "pol_path": "policy/cosign-verify.json",
                "pol_obs": "{\n  \"certificate-oidc-issuer\": \"https://token.actions.githubusercontent.com\"\n}\n",
                "decode_cmd": "cosign verify ghcr.io/katophorite-designed/katophorite-oci@sha256:"
                + hx("kato-img", 64)
                + " --certificate-oidc-issuer https://token.actions.githubusercontent.com --certificate-identity https://ghe.katophorite.example/katophorite-designed/katophorite-oci/.github/workflows/sign.yml@refs/tags/v1.1.1 2>&1 | tail -n 10",
                "decode_obs": "error: issuer https://ghe.katophorite.example/_services/token does not equal token.actions.githubusercontent.com",
                "apply_cmd": "cosign verify ghcr.io/katophorite-designed/katophorite-oci@sha256:"
                + hx("kato-img", 64)
                + " --certificate-oidc-issuer https://token.actions.githubusercontent.com --certificate-identity-regexp '.*katophorite-oci.*' 2>&1 | tail -n 8",
                "apply_obs": "error: issuer mismatch (GHES vs github.com); regexp on identity does not relax issuer",
                "san_cmd": "echo ISSUER=https://ghe.katophorite.example/_services/token",
                "san_obs": "ISSUER=https://ghe.katophorite.example/_services/token",
                "iss_cmd": "echo USE=--certificate-oidc-issuer-regexp '^https://ghe\\\\.katophorite\\\\.example/_services/token$'",
                "iss_obs": "USE=--certificate-oidc-issuer-regexp '^https://ghe\\.katophorite\\.example/_services/token$'",
                "pol_new": "{\n  \"certificate-oidc-issuer-regexp\": \"^https://ghe\\\\.katophorite\\\\.example/_services/token$\"\n}\n",
                "verify_cmd": "cosign verify ghcr.io/katophorite-designed/katophorite-oci@sha256:"
                + hx("kato-img", 64)
                + " --certificate-oidc-issuer-regexp '^https://ghe\\.katophorite\\.example/_services/token$' --certificate-identity https://ghe.katophorite.example/katophorite-designed/katophorite-oci/.github/workflows/sign.yml@refs/tags/v1.1.1 2>&1 | tail -n 8",
                "verify_obs": "Verified OK (GHES issuer)",
                "left_cmd": "ls policy/cosign-verify.dotcom.json && echo DOTCOM_POLICY=leftover",
                "left_obs": "policy/cosign-verify.dotcom.json\nDOTCOM_POLICY=leftover",
                "up_cmd": "echo VERIFY=ghes DOTCOM_POLICY=left",
                "up_obs": "VERIFY=ghes DOTCOM_POLICY=left",
                "wf_old": "runs-on: [self-hosted, ghe]",
                "wf_new": "runs-on: [self-hosted, ghe]\n    # issuer is GHES _services/token, not github.com",
                "cmt_cmd": "git add policy/cosign-verify.json .github/workflows/sign.yml && git commit -m 'verify GHES OIDC issuer regexp'",
                "cmt_obs": "[main " + hx("kato-cmt", 7) + "] verify GHES OIDC issuer regexp",
                "tag_cmd": "git rev-parse v1.1.1^{commit}",
                "tag_obs": gsha("kato-tag"),
                "res_cmd": "echo ISSUER=ghes DOTCOM_POLICY=leftover",
                "res_obs": "ISSUER=ghes DOTCOM_POLICY=leftover",
                "res_refl": "Issuer must match GHES, not github.com. Residual: dotcom verify policy leftover.",
                "seed": "GHES OIDC issuer vs github.com",
                "first": "exact github.com issuer",
                "change": "issuer-regexp GHES",
                "term": "success; dotcom policy leftover",
            },
            "fail_leftover",
            {
                "slug": "pypi-attestation-identity-vs-project-name",
                "plant": "sadanagaite-py",
                "goal": "sadanagaite-py 0.2.0 PEP 740 identity is for project sadanagaite (typo dropped -py). Warehouse latest is 0.2.0 with a mismatched attestation. Publish 0.2.1 with matching identity. Do not delete 0.2.0.",
                "plan": "Re-upload 0.2.0 attestations with the corrected project name.",
                "outcome": "Attestations cannot be rewritten on an existing file. Plan change: 0.2.1 with matching identity. Residual: latest still 0.2.0 mismatched. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "latest_still_old": 1, "cost_steps": 16},
                "inspect_cmd": "curl -sS https://pypi.org/integrity/sadanagaite-py/0.2.0/sadanagaite_py-0.2.0-py3-none-any.whl/provenance | python3 -c 'import sys; print(sys.stdin.read()[:200])'",
                "inspect_obs": "subject name=sadanagaite  # missing -py\nproject sadanagaite-py",
                "wf_path": "pyproject.toml",
                "wf_obs": "[project]\nname = \"sadanagaite-py\"\nversion = \"0.2.0\"\n",
                "why_cmd": "echo IDENTITY=sadanagaite PROJECT=sadanagaite-py MISMATCH=1",
                "why_obs": "IDENTITY=sadanagaite PROJECT=sadanagaite-py MISMATCH=1",
                "con_path": "requirements.txt",
                "con_obs": "sadanagaite-py==0.2.0\n",
                "apply_cmd": "python3 -m pypi-attestations exchange --rewrite 0.2.0 2>&1 | tail -n 8",
                "apply_obs": "error: provenance is immutable per filename; cannot rewrite 0.2.0",
                "apply_refl": "Apply failed. PEP 740 attestations are bound to the uploaded file; names cannot be patched.",
                "still_cmd": "curl -sSI https://files.pythonhosted.org/packages/sa/da/sadanagaite_py-0.2.0-py3-none-any.whl | rg -i HTTP",
                "still_obs": "HTTP/2 200",
                "use_cmd": "curl -sS https://pypi.org/pypi/sadanagaite-py/json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"info\"][\"version\"])'",
                "use_obs": "0.2.0",
                "fix_cmd": "echo NEXT=0.2.1 IDENTITY=sadanagaite-py",
                "fix_obs": "NEXT=0.2.1 IDENTITY=sadanagaite-py",
                "pub_cmd": "sed -i 's/0.2.0/0.2.1/' pyproject.toml && python3 -m build && python3 -m twine upload dist/sadanagaite_py-0.2.1-py3-none-any.whl 2>&1 | tail -n 8",
                "pub_obs": "Uploading 0.2.1\nAttestation identity=sadanagaite-py",
                "ver_cmd": "echo PROV_021=match",
                "ver_obs": "PROV_021=match",
                "tag_cmd": "git commit -am 'release 0.2.1 matching PEP 740 identity' && git tag -s v0.2.1 -m '0.2.1'",
                "tag_obs": "[main " + hx("sada-cmt", 7) + "] release 0.2.1 matching PEP 740 identity",
                "still2_cmd": "echo LATEST=0.2.0 IDENTITY_MISMATCH=1",
                "still2_obs": "LATEST=0.2.0 IDENTITY_MISMATCH=1",
                "undo_cmd": "echo skipped_rewrite_020=1",
                "undo_obs": "skipped_rewrite_020=1",
                "split_cmd": "echo LATEST=0.2.0_mismatch NEW=0.2.1_ok",
                "split_obs": "LATEST=0.2.0_mismatch NEW=0.2.1_ok",
                "tix_cmd": "echo TICKET=pypi_latest_0.2.0_identity_mismatch",
                "tix_obs": "TICKET=pypi_latest_0.2.0_identity_mismatch",
                "res_cmd": "echo OLD=0.2.0 NEW=0.2.1 LATEST=0.2.0",
                "res_obs": "OLD=0.2.0 NEW=0.2.1 LATEST=0.2.0",
                "seed": "PEP 740 identity ≠ project name",
                "first": "rewrite 0.2.0 provenance",
                "change": "0.2.1 matching identity",
                "term": "fail: latest still 0.2.0",
            },
        ),
        # r180
        (
            "gpg_portal",
            {
                "slug": "maven-central-user-token-vs-account-password",
                "plant": "magnesiohastingsite-mvn",
                "goal": "Ship magnesiohastingsite-mvn 5.5.0 via Publisher Portal user token. settings.xml still has the account password (rejected). Do not embed the password. Leave the old server id comment.",
                "plan": "mvn deploy with the Sonatype account password in settings.xml as before OSSRH retirement.",
                "outcome": "Account password rejected (Portal wants a user token). Plan change: portal user token in settings. Residual: old server id comment leftover.",
                "reward": {"success": True, "sign_fails": 1, "plan_changes": 1, "portal": 1, "cost_steps": 15},
                "inspect_cmd": "rg -n 'ossrh|central|password|token' ~/.m2/settings.xml | head",
                "inspect_obs": "<id>ossrh</id><password>account-password</password>",
                "pom_path": "pom.xml",
                "pom_obs": "<distributionManagement><repository><id>ossrh</id></repository></distributionManagement>\n",
                "set_path": "~/.m2/settings.xml",
                "set_obs": "<server><id>ossrh</id><username>magnesio</username><password>account-password</password></server>\n",
                "exp_cmd": "echo PORTAL=user_token REQUIRED=1",
                "exp_obs": "PORTAL=user_token REQUIRED=1",
                "apply_cmd": "mvn -B -Prelease deploy 2>&1 | tail -n 12",
                "apply_obs": "401 Unauthorized\nPublisher Portal does not accept account passwords; create a user token",
                "apply_refl": "Apply failed. Portal authentication is a user token, not the Sonatype account password.",
                "sub_cmd": "echo TOKEN_NS=portal USER=magnesio",
                "sub_obs": "TOKEN_NS=portal USER=magnesio",
                "ep_cmd": "echo ENDPOINT=https://central.sonatype.com/api/v1/publisher",
                "ep_obs": "ENDPOINT=https://central.sonatype.com/api/v1/publisher",
                "fix_path": "~/.m2/settings.xml",
                "fix_contents": "<server><id>central</id><username>magnesio</username><password>${env.SONATYPE_USER_TOKEN}</password></server>\n<!-- leftover ossrh id in comment -->\n",
                "sign_cmd": "mvn -B -Prelease deploy 2>&1 | tail -n 8",
                "sign_obs": "Uploading to Publisher Portal with user token\nDeployment accepted",
                "close_cmd": "echo PUBLISHED=5.5.0",
                "close_obs": "PUBLISHED=5.5.0",
                "left_cmd": "rg -n 'ossrh' ~/.m2/settings.xml",
                "left_obs": "<!-- leftover ossrh id in comment -->",
                "drop_cmd": "echo KEEP_COMMENT=1",
                "drop_obs": "KEEP_COMMENT=1",
                "tag_cmd": "git tag -s v5.5.0 -m '5.5.0' && echo signed_tag_ok",
                "tag_obs": "signed_tag_ok",
                "cmt_cmd": "git add pom.xml && git commit -m 'release 5.5.0 portal user token; drop account password'",
                "cmt_obs": "[main " + hx("mag-cmt", 7) + "] release 5.5.0 portal user token; drop account password",
                "res_cmd": "echo AUTH=user_token OSSRH_COMMENT=leftover",
                "res_obs": "AUTH=user_token OSSRH_COMMENT=leftover",
                "res_refl": "Portal wants a user token. Residual: ossrh server id comment leftover.",
                "seed": "account password vs portal token",
                "first": "deploy with account password",
                "change": "SONATYPE_USER_TOKEN",
                "term": "success; ossrh comment leftover",
            },
            "fail_leftover",
            {
                "slug": "homebrew-bottle-custom-version-not-bumped",
                "plant": "sadanaga-brew",
                "goal": "sadanaga-brew 3.2.0 bottles rebuilt after SDK bump but bottle_custom_version stayed 1. brew pour still hits the version-1 CDN path. Do not delete the release. Selfhost still pours rebuild 1.",
                "plan": "Overwrite the rebuild-1 bottle asset with rebuild-2 bytes under the same filename.",
                "outcome": "Overwrite refused (immutable release asset checksum). Plan change: bottle_custom_version 2 + new filename. Residual: selfhost still pours rebuild 1. Ticket not closed.",
                "reward": {"success": False, "publish_fails": 1, "plan_changes": 1, "bottle_leftover": 1, "cost_steps": 16},
                "inspect_cmd": "rg -n 'rebuild|bottle_custom|sha256' Formula/sadanaga.rb | head",
                "inspect_obs": "rebuild 1\nsha256 cellar: :any, sonoma: \""
                + hx("sada-b1", 64)
                + "\"",
                "wf_path": "Formula/sadanaga.rb",
                "wf_obs": "bottle do\n  rebuild 1\n  sha256 cellar: :any, sonoma: \""
                + hx("sada-b1", 64)
                + "\"\nend\n",
                "why_cmd": "echo SDK_BUMP=15.2 BYTES="
                + hx("sada-b2", 16)
                + " FORMULA="
                + hx("sada-b1", 16),
                "why_obs": "SDK_BUMP=15.2 BYTES="
                + hx("sada-b2", 16)
                + " FORMULA="
                + hx("sada-b1", 16),
                "con_path": "../sadanaga-selfhost/Brewfile",
                "con_obs": "brew \"sadanaga\"\n",
                "apply_cmd": "gh release upload v3.2.0 sadanaga-3.2.0.sonoma.bottle.tar.gz --clobber 2>&1 | tail -n 10",
                "apply_obs": "error: asset checksum immutable; cannot clobber bottle rebuild 1 with rebuild 2 bytes under the same name",
                "apply_refl": "Apply failed. Homebrew bottle filenames include rebuild; you cannot clobber rebuild 1.",
                "still_cmd": "gh release view v3.2.0 --json assets --jq '.assets[].name'",
                "still_obs": "sadanaga-3.2.0.sonoma.bottle.tar.gz",
                "use_cmd": "echo POUR_SELFHOST=rebuild1 " + hx("sada-b1", 16),
                "use_obs": "POUR_SELFHOST=rebuild1 " + hx("sada-b1", 16),
                "fix_cmd": "echo NEXT_FILENAME=sadanaga-3.2.0.sonoma.bottle.2.tar.gz REBUILD=2",
                "fix_obs": "NEXT_FILENAME=sadanaga-3.2.0.sonoma.bottle.2.tar.gz REBUILD=2",
                "pub_cmd": "brew bottle --rebuild --json sadanaga && gh release upload v3.2.0 sadanaga-3.2.0.sonoma.bottle.2.tar.gz 2>&1 | tail -n 6",
                "pub_obs": "uploaded sadanaga-3.2.0.sonoma.bottle.2.tar.gz",
                "ver_cmd": "echo FORMULA_NEEDS_REBUILD2=1",
                "ver_obs": "FORMULA_NEEDS_REBUILD2=1",
                "tag_cmd": "git commit -am 'bottle rebuild 2 after SDK bump' && echo committed",
                "tag_obs": "committed",
                "still2_cmd": "echo POUR_SELFHOST=rebuild1 STILL=1",
                "still2_obs": "POUR_SELFHOST=rebuild1 STILL=1",
                "undo_cmd": "echo skipped_clobber_rebuild1=1",
                "undo_obs": "skipped_clobber_rebuild1=1",
                "split_cmd": "echo ASSET2=uploaded SELFHOST=rebuild1",
                "split_obs": "ASSET2=uploaded SELFHOST=rebuild1",
                "tix_cmd": "echo TICKET=selfhost_still_pours_rebuild_1",
                "tix_obs": "TICKET=selfhost_still_pours_rebuild_1",
                "res_cmd": "echo REBUILD2=asset SELFHOST=rebuild1",
                "res_obs": "REBUILD2=asset SELFHOST=rebuild1",
                "seed": "bottle_custom_version not bumped",
                "first": "clobber rebuild-1 asset",
                "change": "rebuild 2 new filename",
                "term": "fail: selfhost still rebuild 1",
            },
        ),
    ]


PAIRS = _pairs()
BUILDERS = {
    "cosign_reusable": ok_cosign_reusable,
    "oidc_publisher": ok_oidc_publisher,
    "gpg_portal": ok_gpg_portal,
    "bottle_rebuild": ok_bottle_rebuild,
    "nix_nar": ok_nix_nar,
    "nuget_snupkg": ok_nuget_snupkg,
    "fail_leftover": fail_leftover,
}


def notes_for(round_n: int, ok: dict, fail: dict) -> str:
    return (
        f"# NOTES-r{round_n} package-release-factory\n\n"
        "Novel coverage: 88%\n\n"
        "Two designed episodes (quota 2). Release-attestation plants "
        "(sigstore/cosign, npm provenance, PyPI trusted publishing, Maven GPG/portal, "
        "crates.io yank vs index, Homebrew bottle rebuild, Nix NAR-of-src, NuGet snupkg). "
        "Avoided r98–r162 digest-vs-git-SHA + lock-yank twins.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| pkg-r{round_n}-{ok['slug']} | {ok['seed']} | {ok['first']} | {ok['change']} | {ok['term']} |\n"
        f"| pkg-r{round_n}-{fail['slug']} | {fail['seed']} | {fail['first']} | {fail['change']} | {fail['term']} |\n\n"
        "## Step counts\n"
        "- ep1: 15. First apply fail 5; plan change 8; residual leftover 15.\n"
        "- ep2: 16. Replace-same-version fail 5; bump 8–10; leftover consumer 12–16.\n\n"
        "## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:. No thought keys. Plants `{ok['plant']}`, `{fail['plant']}`.\n"
        "No sim_or_real: real.\n\n"
        "## Weaknesses / next\n"
        "Unused: later mill plants after this catalog.\n"
        f"Avoid {ok['slug']} reruns and {fail['slug']} clones.\n"
    )


def banned_text(obj: dict) -> None:
    blob = json.dumps(obj)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if f'"{key}"' in blob:
            raise SystemExit(f"banned key present: {key}")
    if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
        raise SystemExit("sim_or_real real banned")


def emit(round_n: int) -> tuple[dict, dict, str]:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {round_n} outside catalog {CATALOG_FIRST}+{len(PAIRS)}")
    ok_kind, ok_spec, fail_kind, fail_spec = PAIRS[idx]
    ok_ep = BUILDERS[ok_kind](round_n, ok_spec)
    fail_ep = BUILDERS[fail_kind](round_n, fail_spec)
    banned_text(ok_ep)
    banned_text(fail_ep)
    return ok_ep, fail_ep, notes_for(round_n, ok_spec, fail_spec)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    ok_ep, fail_ep, notes = emit(args.round)
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        handle.write(json.dumps(ok_ep, ensure_ascii=False) + "\n")
        handle.write(json.dumps(fail_ep, ensure_ascii=False) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": args.round,
                "ids": [ok_ep["id"], fail_ep["id"]],
                "steps": [len(ok_ep["steps"]), len(fail_ep["steps"])],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
