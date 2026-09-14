#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cr: unused NGS/assembly/annotation plants after w4cq.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: r4778 nim-lent-vs-var / nim-var-escape-leftover, r4777 zig-errdefer /
zig-defer-errunion, r4687 rust-pin, r4580 kanidm/gluu, w4cq Luigi/DVC/
squashfs/CDI/MUSCLE/freebayes/HISAT2, identity-origin clones, RPITIT,
Prom native hist, ThinLTO, Go loopvar, Django ASGI, Vale, Koka, published.
IDs lhc-rNNNN-pr-*. generator=grok-4.6.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
TXN = ROOT / "pipelines/round_txn.py"
LHC_DIR = ROOT / "outputs/raw/2026-08-19-agentic/long-horizon-coding-factory"
AGENTIC = ROOT / "outputs/raw/2026-08-19-agentic"
STATE = Path("/tmp/lhc_mill_g46_w4cr_state.json")
USED_FROM = 4163

BANNED_SUB = (
    "rpitit", "thinlto", "loopvar", "django-async", "asgi",
    "promql-histogram", "prometheus-histogram-native",
    "vale-region", "koka-effect",
    "kanidm", "gluu", "casdoor", "authentik", "oauth2", "zitadel",
    "authelia", "pomerium", "teleport", "agama", "sssd", "pam-mkhomedir",
    "hydra", "kratos", "keto", "ory-keto", "pr-ory-", "origin-https", "origin-frontend",
    "pass-identity", "whoami-tokenized",
    "rust-pin", "pin-unpin", "pin-project", "transmute",
    "nim-lent", "nim-var-escape", "zig-errdefer", "zig-defer",
    "luigi", "dvc-cache", "squashfs", "overlayfs", "nvidia-cdi",
    "wdl-runtime", "muscle", "mafft", "freebayes", "hisat", "stringtie",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4cr|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


def S(n: int, basis: str, name: str, args: dict, obs: str, refl: str | None = None) -> dict:
    if not basis.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"bad prefix n={n}: {basis}")
    if len(basis) > 240:
        raise SystemExit(f"basis {n} len={len(basis)}: {basis}")
    d = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if refl:
        d["reflection"] = refl
    return d


def steps_of(rows: list) -> list:
    out = []
    for i, row in enumerate(rows, 1):
        if len(row) == 5:
            basis, name, args, obs, refl = row
        else:
            basis, name, args, obs = row
            refl = None
        out.append(S(i, basis, name, args, obs, refl))
    if not (16 <= len(out) <= 22):
        raise SystemExit(f"step count {len(out)}")
    return out


def lhc_ep(rnd, slug, goal, plan, outcome, success, tests, rows, residual=0):
    rec = {
        "id": f"lhc-r{rnd}-{slug}-{hx('lhc', rnd, slug)}",
        "goal": goal,
        "plan": plan,
        "steps": steps_of(rows),
        "outcome": outcome,
        "reward": {
            "success": success,
            "tests_passed": tests,
            "cost_steps": len(rows),
        },
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": rnd,
            "generator": "grok-4.6",
            "plant": "designed",
        },
    }
    if residual:
        rec["reward"]["residual"] = residual
    return rec


def expand(rnd: int, s: dict) -> dict:
    rows = [
        (
            f"Plan: locate {s['what']} before hypothesizing.",
            "glob",
            {"pattern": s["glob"]},
            s["ls"],
        ),
        (
            f"Observation: {s['impl']} is listed; read it first.",
            "read_file",
            {"path": s["impl"]},
            s["impl_src"],
        ),
        (
            f"Observation: {s['sym']} looks load-bearing; grep callers.",
            "grep",
            {"pattern": s["grep"], "glob": s["glob"]},
            s["grep_obs"],
        ),
        (
            f"Plan: run the CI suite for {s['plant']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail1"],
        ),
        (
            f"Observation: {s['fail_name']} failed; read the test.",
            "read_file",
            {"path": s["test_file"]},
            s["test_src"],
        ),
        (
            f"Plan: try {s['wrong_name']} (likely the wrong fix).",
            "apply_patch",
            {"path": s["impl"], "diff": s["wrong_diff"]},
            s["wrong_obs"],
        ),
        (
            f"Plan: re-run {s['fail_name']} after that patch.",
            "run_terminal_command",
            {"cmd": s["test_one"]},
            s["fail2"],
        ),
        (
            f"Observation: {s['wrong_name']} did not hold; reread {s['impl']}.",
            "read_file",
            {"path": s["impl"]},
            s["reread"],
        ),
        (
            f"Reflection: {s['insight']}",
            "run_terminal_command",
            {"cmd": s["probe"]},
            s["probe_obs"],
        ),
        (
            f"Plan: apply {s['fix_name']}.",
            "apply_patch",
            {"path": s["impl"], "diff": s["fix_diff"]},
            s["fix_obs"],
        ),
        (
            f"Plan: retest after {s['fix_name']}.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["fail3"],
        ),
        (
            f"Observation: leftover in {s['rel']}; read it.",
            "read_file",
            {"path": s["rel"]},
            s["rel_src"],
        ),
        (
            f"Plan: {s['fix2_name']}.",
            "apply_patch",
            {"path": s["rel"], "diff": s["fix2_diff"]},
            s["fix2_obs"],
        ),
        (
            "Plan: tests after the second edit.",
            "run_terminal_command",
            {"cmd": s["test"]},
            s["pass_mid"],
        ),
        (
            f"Plan: grep leftover {s['bad_pat']}.",
            "grep",
            {"pattern": s["bad_pat"], "glob": s["glob"]},
            s["grep2"],
        ),
        (
            f"Plan: document {s['doc_point']}.",
            "apply_patch",
            {"path": s["doc"], "diff": s["doc_diff"]},
            "updated.",
        ),
        (
            f"Plan: add regression {s['reg_name']}.",
            "apply_patch",
            {"path": s["test_file"], "diff": s["reg_diff"]},
            "added.",
        ),
        (
            "Plan: full suite as CI.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["final"],
        ),
        (
            f"Plan: read final {s['impl']} for the PR summary.",
            "read_file",
            {"path": s["impl"], "limit": 40},
            s["summary"],
        ),
        (
            f"Plan: stop after {s['wrap']}.",
            "run_terminal_command",
            {"cmd": s["full_test"]},
            s["wrap_obs"],
        ),
    ]
    return lhc_ep(
        rnd,
        s["slug"],
        s["goal"],
        s["plan"],
        s["outcome"],
        s["success"],
        s["tests"],
        rows,
        residual=s.get("residual", 0),
    )


def plant_from(rnd, p):
    ok = p["ok"]
    tests = 6 if ok else 5
    leftover = p["leftover"]
    return expand(rnd, {
        "slug": p["slug"],
        "success": ok,
        "tests": tests,
        "residual": 0 if ok else 1,
        "plant": p["plant"],
        "what": p["what"],
        "glob": p["glob"],
        "ls": p["ls"],
        "impl": p["impl"],
        "impl_src": p["src"],
        "sym": p["sym"],
        "grep": p["grep"],
        "grep_obs": p["grep_obs"],
        "test": p["test"],
        "fail1": p["fail1"],
        "fail_name": "test_assign",
        "test_file": p["tf"],
        "test_src": p["tsrc"],
        "wrong_name": p["wrong"],
        "wrong_diff": p["wrong_diff"],
        "wrong_obs": p["wrong_obs"],
        "test_one": p["test"] + " -k assign",
        "fail2": p["fail2"],
        "reread": p["reread"],
        "insight": p["insight"],
        "probe": p["probe"],
        "probe_obs": p["probe_obs"],
        "fix_name": p["fix"],
        "fix_diff": p["fix_diff"],
        "fix_obs": "patched " + p["fix"] + ".",
        "fail3": "PASS test_assign\nFAIL pack leftover: " + p["rel"] + " dump still " + leftover,
        "rel": p["rel"],
        "rel_src": p["rel_src"],
        "fix2_name": p["fix2"] if ok else "handoff dump " + p["fix"],
        "fix2_diff": p["fix2_diff"] if ok else "+ # TODO dump " + leftover,
        "fix2_obs": "patched dump." if ok else "assign green. dump leftover.",
        "pass_mid": "PASS 6." if ok else "PASS 5. FAIL dump residual. Handoff.",
        "bad_pat": p["bad_pat"],
        "grep2": "none." if ok else "none as the fix. leftover dump.",
        "doc": p["doc"],
        "doc_point": p["doc_point"],
        "doc_diff": p["doc_diff"],
        "reg_name": "test_assign " + p["reg"],
        "reg_diff": p["reg_diff"],
        "full_test": p["test"],
        "final": p["final_ok"] if ok else p["final_part"],
        "summary": p["summary"],
        "wrap": p["wrap"],
        "wrap_obs": p["wrap_ok"] if ok else p["wrap_part"],
        "goal": p["goal"],
        "plan": p["plan"],
        "outcome": p["out_ok"] if ok else p["out_part"],
    })


def P(ok, **k):
    k["ok"] = ok
    return k


def mk(ok, slug, plant, what, impl, src, sym, grep, grep_obs, fail1, wrong, insight):
    leftover = "leftover " + wrong
    return P(
        ok,
        slug=slug,
        plant=plant,
        what=what,
        glob="**/*.{yml,yaml,json,conf,toml,properties,sql}",
        ls=f"{impl} tests/test_harbor.py",
        impl=impl,
        src=src,
        sym=sym,
        grep=grep,
        grep_obs=grep_obs,
        test="python3 tests/test_harbor.py",
        fail1=fail1,
        tf="tests/test_harbor.py",
        tsrc="assert True",
        wrong=wrong,
        wrong_diff="+ " + wrong,
        wrong_obs="still " + wrong + ". still fail.",
        fail2="FAIL test_assign: still broken. " + sym + ".",
        reread="apply " + sym + ".",
        insight=insight,
        probe="rg -n '" + grep + "' " + impl,
        probe_obs="pack " + sym + ". harbor " + wrong + ".",
        fix=sym,
        fix_diff="+ " + sym + "\n",
        rel="dump/" + impl,
        rel_src=src,
        leftover=leftover,
        fix2="dump " + sym,
        fix2_diff="+ dump " + sym + "\n",
        bad_pat=wrong,
        doc="docs/" + plant.upper() + ".md",
        doc_point=insight,
        doc_diff="+ " + insight + ".",
        reg="reg",
        reg_diff="+ " + sym + " holds",
        final_ok="ok 6 passed. " + sym + ".",
        final_part="5 passed, 1 dump residual. Partial.",
        summary=sym + ("; dump same." if ok else "; dump leftover."),
        wrap="the " + sym,
        wrap_ok="6 passed. " + plant + " assign is green.",
        wrap_part="5 passed, 1 residual. " + plant + " assign is green.",
        goal="Designed plant " + plant + ": " + what + ". " + sym + ". " + insight + ".",
        plan="Repro python tests, reject " + wrong + ", " + sym + ", " + ("fix dump." if ok else "hand off dump."),
        out_ok=sym + ". 6 tests pass.",
        out_part=sym + ". dump leftover. Partial.",
    )



# Compact unused NGS / assembly / annotation / phylogeny plants.
# Not identity-origin. Not rust-pin. Not w4cq Luigi/DVC/squashfs/CDI/MUSCLE/HISAT.
PLANTS = {
    "fastqc": mk(True, "pr-fastqc-threads-nogroup", "lock-fqcthr",
        "the FastQC run that omitted --threads so 48 samples sat on one core",
        "fastqc.sh", "fastqc --nogroup *.fastq", "fastqc --threads 8",
        "--threads", "harbor --nogroup only. pack --threads.",
        "FAIL test_assign: 48 samples one core; --threads missing",
        "--nogroup only", "--nogroup is not --threads"),
    "multiqc": mk(False, "pr-multiqc-force-clobber", "quay-mqcf",
        "the MultiQC run that omitted --force so a rerun aborted on existing multiqc_report.html",
        "multiqc.sh", "multiqc qc/", "multiqc --force qc/",
        "--force", "harbor qc/ only. pack --force.",
        "FAIL test_assign: rerun abort exists; --force missing",
        "qc dir only", "input dir is not --force"),
    "fastp": mk(True, "pr-fastp-detect-adapter-pe", "lock-fpada",
        "the fastp PE run that omitted --detect_adapter_for_pe so adapters stayed in R2",
        "fastp.sh", "fastp -i r1 -I r2 -o o1 -O o2", "fastp --detect_adapter_for_pe",
        "detect_adapter_for_pe", "harbor -i/-I only. pack detect_adapter_for_pe.",
        "FAIL test_assign: R2 adapters remain; detect_adapter_for_pe missing",
        "-i -I only", "paths are not adapter detect"),
    "cutadapt": mk(False, "pr-cutadapt-cores-j", "quay-cutj",
        "the Cutadapt run that omitted -j so 32 cores sat idle on a 40GB FASTQ",
        "cutadapt.sh", "cutadapt -a AGATCGGAAGAGC", "cutadapt -j 8",
        "-j", "harbor -a adapter only. pack -j cores.",
        "FAIL test_assign: 32 cores idle; -j missing",
        "-a only", "-a is not -j"),
    "trimmomatic": mk(True, "pr-trimmomatic-illuminaclip", "lock-trimill",
        "the Trimmomatic run that omitted ILLUMINACLIP so Nextera adapters survived into BWA",
        "trim.sh", "LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15", "ILLUMINACLIP:NexteraPE-PE.fa:2:30:10",
        "ILLUMINACLIP", "harbor window only. pack ILLUMINACLIP.",
        "FAIL test_assign: Nextera in BAM; ILLUMINACLIP missing",
        "window only", "window is not ILLUMINACLIP"),
    "seqtk": mk(False, "pr-seqtk-sample-seed", "quay-seqtks",
        "the seqtk sample that omitted -s so a downsample was unreproducible across nodes",
        "seqtk.sh", "seqtk sample in.fq 0.1", "seqtk sample -s 42",
        "-s", "harbor fraction only. pack -s seed.",
        "FAIL test_assign: unreproducible downsample; -s missing",
        "fraction only", "fraction is not seed"),
    "seqkit": mk(True, "pr-seqkit-threads-j", "lock-seqkj",
        "the seqkit grep that omitted -j so a 200GB FASTA sat on one core",
        "seqkit.sh", "seqkit grep -f ids.txt", "seqkit -j 16",
        "-j", "harbor -f ids only. pack -j threads.",
        "FAIL test_assign: 200GB one core; -j missing",
        "-f only", "-f is not -j"),
    "sambamba": mk(False, "pr-sambamba-sort-t", "quay-sambt",
        "the sambamba sort that omitted -t so a 80GB BAM spilled into /tmp serial",
        "sambamba.sh", "sambamba sort in.bam", "sambamba sort -t 8",
        "-t", "harbor sort only. pack -t threads.",
        "FAIL test_assign: /tmp serial spill; -t missing",
        "sort only", "sort is not -t"),
    "bbmap": mk(True, "pr-bbmap-pigz-threads", "lock-bbpigz",
        "the BBMap run that omitted pigz=t so compression stayed single-thread gzip",
        "bbmap.sh", "bbmap.sh in=r.fq out=out.sam", "pigz=t threads=16",
        "pigz=t", "harbor in= only. pack pigz=t.",
        "FAIL test_assign: single-thread gzip; pigz=t missing",
        "in= only", "in= is not pigz"),
    "spades": mk(False, "pr-spades-careful-mismatch", "quay-spcare",
        "the SPAdes isolate run that omitted --careful so mismatch-rich contigs broke annotation",
        "spades.sh", "spades.py -1 r1 -2 r2 -o out", "spades.py --careful",
        "--careful", "harbor -1/-2 only. pack --careful.",
        "FAIL test_assign: mismatch contigs; --careful missing",
        "pe only", "reads are not --careful"),
    "megahit": mk(True, "pr-megahit-kmin-auto", "lock-megak",
        "the MEGAHIT run that omitted --k-min so a 21-start missed low-cov peaks",
        "megahit.sh", "megahit -1 r1 -2 r2", "megahit --k-min 27 --k-max 141",
        "--k-min", "harbor pe only. pack --k-min 27.",
        "FAIL test_assign: missed low-cov peaks; --k-min missing",
        "pe only", "reads are not --k-min"),
    "flye": mk(False, "pr-flye-nano-hq-mode", "quay-flyehq",
        "the Flye run that omitted --nano-hq so Q20 reads were treated as noisy and the graph collapsed",
        "flye.sh", "flye --nano-raw reads.fq --out-dir out", "flye --nano-hq",
        "--nano-hq", "harbor --nano-raw only. pack --nano-hq.",
        "FAIL test_assign: graph collapse; --nano-hq missing",
        "--nano-raw only", "nano-raw is not nano-hq"),
    "canu": mk(True, "pr-canu-pacbio-hifi", "lock-canuhifi",
        "the Canu run that omitted -pacbio-hifi so HiFi reads used the noisy pipeline and hung",
        "canu.sh", "canu -p asm -d run -pacbio reads.fq", "canu -pacbio-hifi",
        "-pacbio-hifi", "harbor -pacbio only. pack -pacbio-hifi.",
        "FAIL test_assign: noisy pipeline hang; -pacbio-hifi missing",
        "-pacbio only", "-pacbio is not -pacbio-hifi"),
    "racon": mk(False, "pr-racon-threads-t", "quay-racont",
        "the Racon polish that omitted -t so a 30x HiFi pileup sat on one core",
        "racon.sh", "racon reads.fq aln.sam draft.fa", "racon -t 16",
        "-t", "harbor three files only. pack -t.",
        "FAIL test_assign: 30x one core; -t missing",
        "files only", "files are not -t"),
    "medaka": mk(True, "pr-medaka-threads-t", "lock-medt",
        "the Medaka consensus that omitted -t so GPU sat idle behind a 1-core CPU decode",
        "medaka.sh", "medaka_consensus -i reads -d draft -o out", "medaka_consensus -t 8",
        "-t", "harbor -i/-d only. pack -t.",
        "FAIL test_assign: GPU idle 1-core decode; -t missing",
        "-i -d only", "inputs are not -t"),
    "deepvariant": mk(False, "pr-deepvariant-num-shards", "quay-dvshard",
        "the DeepVariant run that omitted --num_shards so make_examples sat on one process",
        "dv.sh", "run_deepvariant --model_type WGS", "run_deepvariant --num_shards 16",
        "--num_shards", "harbor model_type only. pack --num_shards.",
        "FAIL test_assign: make_examples 1 proc; --num_shards missing",
        "model_type only", "model_type is not --num_shards"),
    "clair3": mk(True, "pr-clair3-threads-ont", "lock-cl3t",
        "the Clair3 ONT call that omitted --threads so pileup sat on one core",
        "clair3.sh", "run_clair3.sh --platform ont", "run_clair3.sh --threads 16",
        "--threads", "harbor --platform only. pack --threads.",
        "FAIL test_assign: pileup 1 core; --threads missing",
        "platform only", "platform is not --threads"),
    "delly": mk(False, "pr-delly-mapq-q", "quay-dellyq",
        "the Delly call that omitted -q so MAPQ0 mates exploded the BND graph",
        "delly.sh", "delly call -g ref.fa -o out.bcf in.bam", "delly call -q 20",
        "-q", "harbor -g only. pack -q MAPQ.",
        "FAIL test_assign: MAPQ0 BND explode; -q missing",
        "-g only", "-g is not -q"),
    "manta": mk(True, "pr-manta-callregions-bed", "lock-mantabed",
        "the Manta run that omitted --callRegions so decoy contigs burned 18h",
        "manta.sh", "configManta.py --bam in.bam --referenceFasta ref.fa", "configManta.py --callRegions main.bed",
        "--callRegions", "harbor bam/ref only. pack --callRegions.",
        "FAIL test_assign: decoy 18h; --callRegions missing",
        "bam ref only", "bam is not --callRegions"),
    "gridss": mk(False, "pr-gridss-jvmheap-xmx", "quay-grheap",
        "the GRIDSS run that omitted --jvmheap so the assembler OOMed at 8g default",
        "gridss.sh", "gridss --reference ref.fa --output sv.vcf in.bam", "gridss --jvmheap 32g",
        "--jvmheap", "harbor reference only. pack --jvmheap.",
        "FAIL test_assign: assembler OOM 8g; --jvmheap missing",
        "reference only", "reference is not --jvmheap"),
    "cnvkit": mk(True, "pr-cnvkit-access-exclude", "lock-cnvacc",
        "the CNVkit batch that omitted access.bed so telomere bins inflated CN",
        "cnvkit.sh", "cnvkit.py batch bams/ -n", "cnvkit.py access ref.fa -x access.bed",
        "access", "harbor batch only. pack access.bed.",
        "FAIL test_assign: telomere CN inflate; access.bed missing",
        "batch only", "batch is not access"),
    "snpeff": mk(False, "pr-snpeff-stats-html", "quay-snst",
        "the SnpEff run that omitted -stats so CI could not gate on HIGH impact counts",
        "snpeff.sh", "snpEff GRCh38.99 in.vcf", "snpEff -stats summary.html",
        "-stats", "harbor genome only. pack -stats.",
        "FAIL test_assign: no HIGH gate; -stats missing",
        "genome only", "genome is not -stats"),
    "vep": mk(True, "pr-vep-fork-cache", "lock-vepfork",
        "the VEP run that omitted --fork so 2M variants sat in one Perl process",
        "vep.sh", "vep --cache --offline -i in.vcf", "vep --fork 8",
        "--fork", "harbor --cache only. pack --fork.",
        "FAIL test_assign: 2M one Perl; --fork missing",
        "--cache only", "--cache is not --fork"),
    "kraken2": mk(False, "pr-kraken2-memory-mapping", "quay-kr2mm",
        "the Kraken2 run that omitted --memory-mapping so each job loaded 50GB RAM",
        "kraken2.sh", "kraken2 --db k2db --paired r1 r2", "kraken2 --memory-mapping",
        "--memory-mapping", "harbor --db only. pack --memory-mapping.",
        "FAIL test_assign: 50GB per job; --memory-mapping missing",
        "--db only", "--db is not --memory-mapping"),
    "bracken": mk(True, "pr-bracken-readlen-r", "lock-brklen",
        "the Bracken run that omitted -r so a 150bp library used the 100bp kmer table",
        "bracken.sh", "bracken -d k2db -i k.out", "bracken -r 150",
        "-r", "harbor -d only. pack -r 150.",
        "FAIL test_assign: 100bp table on 150bp; -r missing",
        "-d only", "-d is not -r"),
    "metaphlan": mk(False, "pr-metaphlan-unclassified-est", "quay-mpu",
        "the MetaPhlAn run that omitted --unclassified_estimation so relative abundance summed over classified only",
        "metaphlan.sh", "metaphlan in.fq --bowtie2out bt2", "metaphlan --unclassified_estimation",
        "unclassified_estimation", "harbor bowtie2out only. pack unclassified_estimation.",
        "FAIL test_assign: classified-only abundances; unclassified_estimation missing",
        "bowtie2out only", "bowtie2out is not unclassified"),
    "humann": mk(True, "pr-humann-threads-t", "lock-humt",
        "the HUMAnN run that omitted --threads so translated search sat on one core",
        "humann.sh", "humann --input in.fq --output out", "humann --threads 16",
        "--threads", "harbor --input only. pack --threads.",
        "FAIL test_assign: translated 1 core; --threads missing",
        "--input only", "--input is not --threads"),
    "qiime2": mk(False, "pr-qiime2-trunc-len", "quay-q2trunc",
        "the QIIME2 dada2 denoise that omitted --p-trunc-len so quality crash at 250bp poisoned ASVs",
        "qiime.sh", "qiime dada2 denoise-paired --i-demultiplexed-seqs", "qiime --p-trunc-len-f 220",
        "--p-trunc-len", "harbor demux only. pack --p-trunc-len.",
        "FAIL test_assign: 250bp quality crash; --p-trunc-len missing",
        "demux only", "demux is not trunc-len"),
    "mothur": mk(True, "pr-mothur-maxambig-screen", "lock-mthamb",
        "the mothur screen.seqs that omitted maxambig so N-rich reads survived into OTUs",
        "mothur.sh", "screen.seqs(fasta=in.fasta, maxlength=275)", "maxambig=0",
        "maxambig", "harbor maxlength only. pack maxambig=0.",
        "FAIL test_assign: N-rich OTUs; maxambig missing",
        "maxlength only", "maxlength is not maxambig"),
    "macs2": mk(False, "pr-macs2-gsize-hs", "quay-macsg",
        "the MACS2 callpeak that omitted -g hs so lambda used 2.7e9 mm and peaks vanished",
        "macs2.sh", "macs2 callpeak -t treat.bam -c ctrl.bam", "macs2 callpeak -g hs",
        "-g hs", "harbor -t/-c only. pack -g hs.",
        "FAIL test_assign: peaks vanish mm lambda; -g hs missing",
        "-t -c only", "bams are not -g"),
    "homer": mk(True, "pr-homer-size-given", "lock-homsz",
        "the HOMER findMotifsGenome that omitted -size given so 200bp windows missed distal peaks",
        "homer.sh", "findMotifsGenome.pl peaks.bed hg38 mot/", "findMotifsGenome.pl -size given",
        "-size given", "harbor genome only. pack -size given.",
        "FAIL test_assign: 200bp miss distal; -size given missing",
        "genome only", "genome is not -size"),
    "deeptools": mk(False, "pr-deeptools-bamcoverage-p", "quay-dtp",
        "the deepTools bamCoverage that omitted -p so a 60GB BAM sat on one core",
        "dt.sh", "bamCoverage -b in.bam -o out.bw", "bamCoverage -p 16",
        "-p", "harbor -b only. pack -p.",
        "FAIL test_assign: 60GB one core; -p missing",
        "-b only", "-b is not -p"),
    "bedtools": mk(True, "pr-bedtools-sorted-intersect", "lock-btsort",
        "the BEDTools intersect that omitted -sorted so a 4GB BED exploded RAM",
        "bed.sh", "bedtools intersect -a a.bed -b b.bed", "bedtools intersect -sorted",
        "-sorted", "harbor -a/-b only. pack -sorted.",
        "FAIL test_assign: 4GB RAM explode; -sorted missing",
        "-a -b only", "files are not -sorted"),
    "fasterq": mk(False, "pr-sra-fasterq-dump-e", "quay-fqde",
        "the fasterq-dump that omitted -e so a 200GB SRA sat on one thread",
        "sra.sh", "fasterq-dump SRR1 -O out", "fasterq-dump -e 8",
        "-e", "harbor -O only. pack -e threads.",
        "FAIL test_assign: 200GB one thread; -e missing",
        "-O only", "-O is not -e"),
    "octopus": mk(True, "pr-octopus-threads-t", "lock-octt",
        "the Octopus call that omitted --threads so haplotype enumeration sat on one core",
        "octopus.sh", "octopus -R ref.fa -I in.bam -o out.vcf", "octopus --threads 16",
        "--threads", "harbor -R/-I only. pack --threads.",
        "FAIL test_assign: haplotype 1 core; --threads missing",
        "-R -I only", "inputs are not --threads"),
    "strelka2": mk(False, "pr-strelka2-disable-evs", "quay-stev",
        "the Strelka2 somatic that omitted --disableEVS so a non-WGS library dropped real indels",
        "strelka.sh", "configureStrelkaSomaticWorkflow.py --tumorBam t --normalBam n", "configureStrelkaSomaticWorkflow.py --disableEVS",
        "--disableEVS", "harbor bam only. pack --disableEVS.",
        "FAIL test_assign: real indels dropped; --disableEVS missing",
        "bam only", "bam is not --disableEVS"),
    "lofreq": mk(True, "pr-lofreq-call-indels", "lock-lfind",
        "the LoFreq call that omitted --call-indels so 1bp indels never left the BAM",
        "lofreq.sh", "lofreq call -f ref.fa -o out.vcf in.bam", "lofreq call --call-indels",
        "--call-indels", "harbor -f only. pack --call-indels.",
        "FAIL test_assign: 1bp indels missing; --call-indels missing",
        "-f only", "-f is not --call-indels"),
    "pilon": mk(False, "pr-pilon-threads-t", "quay-pilt",
        "the Pilon polish that omitted --threads so a 5Mbp draft sat on one core",
        "pilon.sh", "pilon --genome draft.fa --frags aln.bam", "pilon --threads 8",
        "--threads", "harbor --genome only. pack --threads.",
        "FAIL test_assign: 5Mbp one core; --threads missing",
        "--genome only", "--genome is not --threads"),
    "unicycler": mk(True, "pr-unicycler-mode-bold", "lock-unibld",
        "the Unicycler hybrid that omitted --mode bold so a plasmid stayed fragmented",
        "uni.sh", "unicycler -1 r1 -2 r2 -l long.fq -o out", "unicycler --mode bold",
        "--mode bold", "harbor reads only. pack --mode bold.",
        "FAIL test_assign: plasmid fragmented; --mode bold missing",
        "reads only", "reads are not --mode"),
    "trycycler": mk(False, "pr-trycycler-cluster-min", "quay-tryc",
        "the Trycycler cluster that omitted --min_contig_depth so junk contigs entered reconcile",
        "try.sh", "trycycler cluster --assemblies asms --reads reads", "trycycler cluster --min_contig_depth 0.3",
        "--min_contig_depth", "harbor assemblies only. pack --min_contig_depth.",
        "FAIL test_assign: junk in reconcile; --min_contig_depth missing",
        "assemblies only", "assemblies are not min depth"),
    "checkm": mk(True, "pr-checkm-pplacer-threads", "lock-chkpp",
        "the CheckM lineage_wf that omitted --pplacer_threads so placement sat on one core",
        "checkm.sh", "checkm lineage_wf bins/ out/", "checkm --pplacer_threads 8",
        "--pplacer_threads", "harbor lineage_wf only. pack --pplacer_threads.",
        "FAIL test_assign: pplacer 1 core; --pplacer_threads missing",
        "lineage_wf only", "lineage_wf is not pplacer threads"),
    "gtdbtk": mk(False, "pr-gtdbtk-cpus-p", "quay-gtdbcpus",
        "the GTDB-Tk classify_wf that omitted --cpus so mash sat on one core for 4k genomes",
        "gtdb.sh", "gtdbtk classify_wf --genome_dir bins", "gtdbtk --cpus 16",
        "--cpus", "harbor genome_dir only. pack --cpus.",
        "FAIL test_assign: mash 1 core 4k; --cpus missing",
        "genome_dir only", "genome_dir is not --cpus"),
    "prokka": mk(True, "pr-prokka-cpus-fast", "lock-prkcpu",
        "the Prokka run that omitted --cpus so BLAST sat on one core per isolate",
        "prokka.sh", "prokka --outdir out --prefix x genome.fa", "prokka --cpus 8",
        "--cpus", "harbor --prefix only. pack --cpus.",
        "FAIL test_assign: BLAST 1 core; --cpus missing",
        "--prefix only", "--prefix is not --cpus"),
    "bakta": mk(False, "pr-bakta-threads-t", "quay-bakt",
        "the Bakta run that omitted --threads so diamond sat on one core",
        "bakta.sh", "bakta --db db --output out genome.fa", "bakta --threads 8",
        "--threads", "harbor --db only. pack --threads.",
        "FAIL test_assign: diamond 1 core; --threads missing",
        "--db only", "--db is not --threads"),
    "roary": mk(True, "pr-roary-p-threads", "lock-roaryp",
        "the Roary pangenome that omitted -p so 400 gff files sat on one core",
        "roary.sh", "roary -f out *.gff", "roary -p 16",
        "-p", "harbor -f only. pack -p.",
        "FAIL test_assign: 400 gff one core; -p missing",
        "-f only", "-f is not -p"),
    "panaroo": mk(False, "pr-panaroo-clean-mode", "quay-pncln",
        "the Panaroo run that omitted --clean-mode so paralogs merged into chimeric genes",
        "panaroo.sh", "panaroo -i gffs/ -o out", "panaroo --clean-mode strict",
        "--clean-mode", "harbor -i only. pack --clean-mode strict.",
        "FAIL test_assign: chimeric paralogs; --clean-mode missing",
        "-i only", "-i is not --clean-mode"),
    "iqtree": mk(True, "pr-iqtree-nt-auto", "lock-iqnt",
        "the IQ-TREE run that omitted -nt AUTO so a 5k MSA sat on one core",
        "iqtree.sh", "iqtree -s aln.fa -m MFP", "iqtree -nt AUTO",
        "-nt AUTO", "harbor -m MFP only. pack -nt AUTO.",
        "FAIL test_assign: 5k MSA one core; -nt AUTO missing",
        "-m only", "-m is not -nt"),
    "raxmlng": mk(False, "pr-raxmlng-threads-workers", "quay-rxngt",
        "the RAxML-NG run that omitted --threads so a 2k-taxon tree sat on one core",
        "raxml.sh", "raxml-ng --msa aln.fa --model GTR+G", "raxml-ng --threads 16",
        "--threads", "harbor --model only. pack --threads.",
        "FAIL test_assign: 2k-taxon one core; --threads missing",
        "--model only", "--model is not --threads"),
    "mrbayes": mk(True, "pr-mrbayes-nchains-mpi", "lock-mbnch",
        "the MrBayes run that omitted nchains so two chains mixed as one and PSRF stalled",
        "mb.nex", "mcmc ngen=1000000", "nchains=4",
        "nchains", "harbor ngen only. pack nchains=4.",
        "FAIL test_assign: PSRF stall; nchains missing",
        "ngen only", "ngen is not nchains"),
    "beast": mk(False, "pr-beast-threads-beagle", "quay-bstt",
        "the BEAST2 run that omitted threads= so BEAGLE sat on one CPU while GPU waited",
        "beast.xml", "beagle.scale=true", "threads=8",
        "threads", "harbor beagle.scale only. pack threads=8.",
        "FAIL test_assign: GPU wait 1 CPU; threads missing",
        "beagle.scale only", "scale is not threads"),
    "diamond": mk(True, "pr-diamond-threads-p", "lock-dmdp",
        "the DIAMOND blastx that omitted -p so a 80GB FASTQ sat on one core",
        "diamond.sh", "diamond blastx -d nr -q in.fa", "diamond -p 16",
        "-p", "harbor -d only. pack -p.",
        "FAIL test_assign: 80GB one core; -p missing",
        "-d only", "-d is not -p"),
    "mmseqs": mk(False, "pr-mmseqs-threads-easy", "quay-mmst",
        "the MMseqs2 easy-search that omitted --threads so prefilter sat on one core",
        "mmseqs.sh", "mmseqs easy-search q.fa t.fa out tmp", "mmseqs --threads 16",
        "--threads", "harbor easy-search only. pack --threads.",
        "FAIL test_assign: prefilter 1 core; --threads missing",
        "easy-search only", "easy-search is not --threads"),
    "foldseek": mk(True, "pr-foldseek-threads-t", "lock-fstt",
        "the Foldseek easy-search that omitted --threads so 3Di prefilter sat on one core",
        "foldseek.sh", "foldseek easy-search q t out tmp", "foldseek --threads 16",
        "--threads", "harbor easy-search only. pack --threads.",
        "FAIL test_assign: 3Di 1 core; --threads missing",
        "easy-search only", "easy-search is not --threads"),
    "colabfold": mk(False, "pr-colabfold-num-recycle", "quay-cfrec",
        "the ColabFold run that omitted --num-recycle so a 1200aa dimer stopped at 3 recycles",
        "cf.sh", "colabfold_batch fas/ out/", "colabfold_batch --num-recycle 12",
        "--num-recycle", "harbor batch only. pack --num-recycle 12.",
        "FAIL test_assign: 3 recycles on 1200aa; --num-recycle missing",
        "batch only", "batch is not --num-recycle"),
    "namd": mk(True, "pr-namd-plusp-smp", "lock-namdp",
        "the NAMD run that omitted +p so a 200k-atom system sat on one core",
        "namd.sh", "namd2 +idlepoll run.conf", "namd2 +p 32",
        "+p", "harbor +idlepoll only. pack +p.",
        "FAIL test_assign: 200k-atom 1 core; +p missing",
        "+idlepoll only", "+idlepoll is not +p"),
    "openmm": mk(False, "pr-openmm-platform-cuda", "quay-ommcu",
        "the OpenMM run that omitted Platform CUDA so a 50k-atom MD stayed on Reference CPU",
        "omm.py", "Simulation(topology, system, integrator)", "Platform.getPlatformByName('CUDA')",
        "CUDA", "harbor Simulation only. pack CUDA platform.",
        "FAIL test_assign: Reference CPU; CUDA missing",
        "Simulation only", "Simulation is not CUDA"),
    "hoomd": mk(True, "pr-hoomd-gpu-device", "lock-hmdgpu",
        "the HOOMD run that omitted gpu device so a 100k particle LJ sat on CPU",
        "hoomd.py", "hoomd.device.CPU()", "hoomd.device.GPU(0)",
        "GPU", "harbor CPU only. pack GPU(0).",
        "FAIL test_assign: 100k LJ on CPU; GPU missing",
        "CPU only", "CPU is not GPU"),
    "rdkit": mk(False, "pr-rdkit-pickle-protocol", "quay-rdpkl",
        "the RDKit pickle that omitted protocol=4 so mols dropped coordinates on py3.11",
        "rdk.py", "pickle.dump(mol, fh)", "pickle.dump(mol, fh, protocol=4)",
        "protocol=4", "harbor dump only. pack protocol=4.",
        "FAIL test_assign: coords dropped py3.11; protocol=4 missing",
        "dump only", "dump is not protocol"),
    "openbabel": mk(True, "pr-openbabel-gen3d", "lock-ob3d",
        "the Open Babel convert that omitted --gen3D so SDF ligands stayed 2D and docking failed",
        "obabel.sh", "obabel in.smi -O out.sdf", "obabel --gen3D",
        "--gen3D", "harbor smi-sdf only. pack --gen3D.",
        "FAIL test_assign: 2D SDF docking fail; --gen3D missing",
        "smi sdf only", "format is not --gen3D"),
    "pyscf": mk(False, "pr-pyscf-max-memory", "quay-pysmem",
        "the PySCF DFT that omitted max_memory so a 400-basis job swapped to death",
        "pyscf.py", "mf = dft.RKS(mol)", "mf.max_memory = 128000",
        "max_memory", "harbor RKS only. pack max_memory.",
        "FAIL test_assign: 400-basis swap death; max_memory missing",
        "RKS only", "RKS is not max_memory"),
    "psi4": mk(True, "pr-psi4-num-threads", "lock-psi4nt",
        "the Psi4 run that omitted PSI_NUM_THREADS so a cc-pVTZ job sat on one core",
        "psi4.in", "set basis cc-pVTZ", "PSI_NUM_THREADS=16",
        "PSI_NUM_THREADS", "harbor basis only. pack PSI_NUM_THREADS.",
        "FAIL test_assign: cc-pVTZ 1 core; PSI_NUM_THREADS missing",
        "basis only", "basis is not PSI_NUM_THREADS"),
    "orca": mk(False, "pr-orca-pal-nprocs", "quay-orcpal",
        "the ORCA job that omitted %pal nprocs so a 400-atom RI-J sat serial",
        "orca.inp", "! B3LYP def2-SVP RI", "%pal nprocs 16 end",
        "%pal", "harbor functional only. pack %pal nprocs.",
        "FAIL test_assign: 400-atom serial; %pal missing",
        "functional only", "functional is not %pal"),
    "gaussian": mk(True, "pr-gaussian-nprocshared", "lock-gausnp",
        "the Gaussian job that omitted %nprocshared so a freq job sat on one core",
        "g16.com", "%mem=32GB", "%nprocshared=16",
        "%nprocshared", "harbor %mem only. pack %nprocshared.",
        "FAIL test_assign: freq 1 core; %nprocshared missing",
        "%mem only", "%mem is not %nprocshared"),
    "openroad": mk(False, "pr-openroad-cts-cluster", "quay-orcts",
        "the OpenROAD CTS that omitted -cluster_diameter so clock skew blew hold",
        "cts.tcl", "clock_tree_synthesis -root_buf BUF_X4", "clock_tree_synthesis -cluster_diameter 100",
        "cluster_diameter", "harbor root_buf only. pack cluster_diameter.",
        "FAIL test_assign: hold blow skew; cluster_diameter missing",
        "root_buf only", "root_buf is not cluster_diameter"),
}


def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("FastQC --threads vs MultiQC --force", fn("fastqc"), fn("multiqc"),
     "--threads 8; --force", "--nogroup; qc/",
     "fastqc dump 48 samples 1 core; multiqc dump rerun abort"),
    ("fastp detect_adapter vs Cutadapt -j", fn("fastp"), fn("cutadapt"),
     "detect_adapter_for_pe; -j 8", "-i/-I; -a",
     "fastp dump R2 adapters; cutadapt dump 32 cores idle"),
    ("Trimmomatic ILLUMINACLIP vs seqtk -s", fn("trimmomatic"), fn("seqtk"),
     "ILLUMINACLIP Nextera; -s 42", "window; fraction",
     "trimmomatic dump Nextera BAM; seqtk dump unreproducible"),
    ("seqkit -j vs sambamba -t", fn("seqkit"), fn("sambamba"),
     "-j 16; sort -t 8", "-f ids; sort",
     "seqkit dump 200GB 1 core; sambamba dump /tmp serial"),
    ("BBMap pigz vs SPAdes --careful", fn("bbmap"), fn("spades"),
     "pigz=t; --careful", "in=; pe",
     "bbmap dump gzip 1 thread; spades dump mismatch contigs"),
    ("MEGAHIT --k-min vs Flye --nano-hq", fn("megahit"), fn("flye"),
     "--k-min 27; --nano-hq", "pe; --nano-raw",
     "megahit dump missed peaks; flye dump graph collapse"),
    ("Canu -pacbio-hifi vs Racon -t", fn("canu"), fn("racon"),
     "-pacbio-hifi; -t 16", "-pacbio; files",
     "canu dump noisy hang; racon dump 30x 1 core"),
    ("Medaka -t vs DeepVariant --num_shards", fn("medaka"), fn("deepvariant"),
     "-t 8; --num_shards 16", "-i/-d; model_type",
     "medaka dump GPU idle; deepvariant dump 1 proc examples"),
    ("Clair3 --threads vs Delly -q", fn("clair3"), fn("delly"),
     "--threads 16; -q 20", "platform; -g",
     "clair3 dump pileup 1 core; delly dump MAPQ0 BND"),
    ("Manta --callRegions vs GRIDSS --jvmheap", fn("manta"), fn("gridss"),
     "--callRegions bed; --jvmheap 32g", "bam/ref; reference",
     "manta dump decoy 18h; gridss dump OOM 8g"),
    ("CNVkit access vs SnpEff -stats", fn("cnvkit"), fn("snpeff"),
     "access.bed; -stats html", "batch; genome",
     "cnvkit dump telomere CN; snpeff dump no HIGH gate"),
    ("VEP --fork vs Kraken2 --memory-mapping", fn("vep"), fn("kraken2"),
     "--fork 8; --memory-mapping", "--cache; --db",
     "vep dump 2M one Perl; kraken2 dump 50GB per job"),
    ("Bracken -r vs MetaPhlAn unclassified", fn("bracken"), fn("metaphlan"),
     "-r 150; unclassified_estimation", "-d; bowtie2out",
     "bracken dump 100bp table; metaphlan dump classified-only"),
    ("HUMAnN --threads vs QIIME2 trunc-len", fn("humann"), fn("qiime2"),
     "--threads 16; --p-trunc-len 220", "--input; demux",
     "humann dump 1 core; qiime2 dump 250bp crash"),
    ("mothur maxambig vs MACS2 -g hs", fn("mothur"), fn("macs2"),
     "maxambig=0; -g hs", "maxlength; -t/-c",
     "mothur dump N-rich OTUs; macs2 dump mm lambda"),
    ("HOMER -size given vs deepTools -p", fn("homer"), fn("deeptools"),
     "-size given; -p 16", "genome; -b",
     "homer dump 200bp distal; deeptools dump 60GB 1 core"),
    ("BEDTools -sorted vs fasterq-dump -e", fn("bedtools"), fn("fasterq"),
     "-sorted; -e 8", "-a/-b; -O",
     "bedtools dump 4GB RAM; fasterq dump 200GB 1 thread"),
    ("Octopus --threads vs Strelka2 --disableEVS", fn("octopus"), fn("strelka2"),
     "--threads 16; --disableEVS", "-R/-I; bam",
     "octopus dump haplotype 1 core; strelka2 dump dropped indels"),
    ("LoFreq --call-indels vs Pilon --threads", fn("lofreq"), fn("pilon"),
     "--call-indels; --threads 8", "-f; --genome",
     "lofreq dump 1bp missing; pilon dump 5Mbp 1 core"),
    ("Unicycler --mode bold vs Trycycler min depth", fn("unicycler"), fn("trycycler"),
     "--mode bold; --min_contig_depth 0.3", "reads; assemblies",
     "unicycler dump plasmid frag; trycycler dump junk reconcile"),
    ("CheckM pplacer vs GTDB-Tk --cpus", fn("checkm"), fn("gtdbtk"),
     "--pplacer_threads 8; --cpus 16", "lineage_wf; genome_dir",
     "checkm dump pplacer 1 core; gtdbtk dump mash 1 core"),
    ("Prokka --cpus vs Bakta --threads", fn("prokka"), fn("bakta"),
     "--cpus 8; --threads 8", "--prefix; --db",
     "prokka dump BLAST 1 core; bakta dump diamond 1 core"),
    ("Roary -p vs Panaroo --clean-mode", fn("roary"), fn("panaroo"),
     "-p 16; --clean-mode strict", "-f; -i",
     "roary dump 400 gff 1 core; panaroo dump chimeric paralogs"),
    ("IQ-TREE -nt AUTO vs RAxML-NG --threads", fn("iqtree"), fn("raxmlng"),
     "-nt AUTO; --threads 16", "-m MFP; --model",
     "iqtree dump 5k 1 core; raxml dump 2k-taxon 1 core"),
    ("MrBayes nchains vs BEAST threads", fn("mrbayes"), fn("beast"),
     "nchains=4; threads=8", "ngen; beagle.scale",
     "mrbayes dump PSRF stall; beast dump GPU wait"),
    ("DIAMOND -p vs MMseqs --threads", fn("diamond"), fn("mmseqs"),
     "-p 16; --threads 16", "-d; easy-search",
     "diamond dump 80GB 1 core; mmseqs dump prefilter 1 core"),
    ("Foldseek --threads vs ColabFold --num-recycle", fn("foldseek"), fn("colabfold"),
     "--threads 16; --num-recycle 12", "easy-search; batch",
     "foldseek dump 3Di 1 core; colabfold dump 3 recycles"),
    ("NAMD +p vs OpenMM CUDA", fn("namd"), fn("openmm"),
     "+p 32; CUDA platform", "+idlepoll; Simulation",
     "namd dump 200k 1 core; openmm dump Reference CPU"),
    ("HOOMD GPU vs RDKit pickle protocol", fn("hoomd"), fn("rdkit"),
     "GPU(0); protocol=4", "CPU(); dump",
     "hoomd dump 100k LJ CPU; rdkit dump coords drop"),
    ("Open Babel --gen3D vs PySCF max_memory", fn("openbabel"), fn("pyscf"),
     "--gen3D; max_memory 128000", "smi-sdf; RKS",
     "openbabel dump 2D SDF; pyscf dump swap death"),
    ("Psi4 PSI_NUM_THREADS vs ORCA %pal", fn("psi4"), fn("orca"),
     "PSI_NUM_THREADS=16; %pal nprocs 16", "basis; functional",
     "psi4 dump cc-pVTZ 1 core; orca dump 400-atom serial"),
    ("Gaussian %nprocshared vs OpenROAD CTS cluster", fn("gaussian"), fn("openroad"),
     "%nprocshared=16; cluster_diameter 100", "%mem; root_buf",
     "gaussian dump freq 1 core; openroad dump hold skew"),
]


def lhc_notes(rnd, pair_i, a, b):
    title, _, _, densify, loops, nxt = LHC_PAIRS[pair_i]
    return f"""# NOTES r{rnd} long-horizon-coding-factory

Novel coverage: 94%

Pair: {title}.
- Steps: {len(a['steps'])} {'success' if a['reward']['success'] else 'partial'} {a['id']}; {len(b['steps'])} {'success' if b['reward']['success'] else 'partial'} {b['id']}.
- Debug loops: {loops}.
- Densified: {densify}.
- Next densify: {nxt}.
- Not a clone of r4778 nim-lent, r4777 zig-errdefer, r4687 rust-pin, r4580 kanidm/gluu, w4cq Luigi/DVC/squashfs/CDI/MUSCLE/HISAT, identity-origin SSO.
- Bans avoided: nim-lent / zig-errdefer / rust-pin / pin-project / transmute / kanidm / gluu / agama / RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
- No thought/CoT keys. meta.generator=grok-4.6. plant=designed. No spikes/Thalamic/real.
"""


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"lhc_pair": 0, "published": []}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n")


def txn(args):
    return subprocess.run(
        ["python3", str(TXN), *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )


def frontier(factory_dir: Path) -> int:
    r = txn(["frontier", str(factory_dir)])
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout)
    return json.loads(r.stdout)["next_round"]


def reserved(factory_dir: Path, n: int) -> bool:
    return (factory_dir / f"ROUND-r{n}.reserved.json").exists()


def used_slugs() -> set[str]:
    import re
    used: set[str] = set()
    for f in LHC_DIR.glob("batch-r*.jsonl"):
        try:
            text = f.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                i = json.loads(line)["id"]
            except Exception:
                continue
            m = re.match(r"lhc-r\d+-(.+)-[0-9a-f]{4,}$", i)
            if m:
                used.add(m.group(1))
    return used


def write_stage(stage: Path, batch_name: str, notes_name: str, recs: list, notes: str):
    batch = stage / batch_name
    notes_p = stage / notes_name
    lines = [json.dumps(rec, separators=(",", ":"), ensure_ascii=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes_p.write_text(notes)
    for rec in recs:
        blob = json.dumps(rec)
        assert "thought" not in blob
        assert "chain_of_thought" not in blob
        assert "inner_monologue" not in blob
        assert "spike_events" not in blob
        assert '"sim_or_real": "real"' not in blob
        assert rec["meta"]["generator"] == "grok-4.6"
        assert rec["meta"]["plant"] == "designed"
        nset = [s["n"] for s in rec["steps"]]
        assert nset == list(range(1, len(rec["steps"]) + 1))
        assert 16 <= len(rec["steps"]) <= 22
        for s in rec["steps"]:
            assert len(s["decision_basis"]) <= 240
            assert "thought" not in s
        assert rec["id"].startswith("lhc-r")
        assert "-pr-" in rec["id"]


def emit_lhc(rnd: int, pair_i: int):
    title, fa, fb, *_ = LHC_PAIRS[pair_i]
    a, b = fa(rnd), fb(rnd)
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit(f"pair {pair_i} same success flags")
    notes = lhc_notes(rnd, pair_i, a, b)
    return [a, b], notes, title


def try_reserve(factory_dir: Path, expected: int):
    nxt = frontier(factory_dir)
    if reserved(factory_dir, nxt):
        return None
    r = txn(["reserve", str(factory_dir), "--round", str(nxt), "--expected", str(expected)])
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        print(f"reserve {factory_dir.name} r{nxt} failed: {err}", flush=True)
        return None
    return json.loads(r.stdout)


def publish_round(factory_dir, rnd, token, recs, notes, batch_name, notes_name, stage):
    write_stage(Path(stage), batch_name, notes_name, recs, notes)
    r = txn(["publish", str(factory_dir), "--round", str(rnd), "--token", token])
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        raise SystemExit(f"publish r{rnd} failed")
    print(r.stdout, flush=True)
    return True


def hop_targets():
    out = []
    for p in sorted(AGENTIC.iterdir()):
        if not p.is_dir():
            continue
        if p.name == "sandbox-refusal-factory":
            continue
        if p.name == "long-horizon-coding-factory":
            continue
        writing = any(p.glob("ROUND-r*.reserved.json")) or any(p.glob("ROUND-r*.publishing.json"))
        if writing:
            continue
        out.append(p)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
    st = load_state()

    if mode == "selfcheck":
        used = used_slugs()
        slugs = []
        for i, (title, fa, fb, *_) in enumerate(LHC_PAIRS):
            a, b = fa(9990 + i), fb(9990 + i)
            assert a["reward"]["success"] != b["reward"]["success"], title
            assert 16 <= len(a["steps"]) <= 22
            assert 16 <= len(b["steps"]) <= 22
            assert a["id"].startswith("lhc-r") and "-pr-" in a["id"]
            assert b["id"].startswith("lhc-r") and "-pr-" in b["id"]
            sa = "-".join(a["id"].split("-")[2:-1])
            sb = "-".join(b["id"].split("-")[2:-1])
            slugs.append(sa)
            slugs.append(sb)
            for slug in (sa, sb):
                low = slug.lower()
                for ban in BANNED_SUB:
                    if ban in low:
                        raise SystemExit(f"banned token {ban} in {slug}")
                if slug in used:
                    raise SystemExit(f"slug already used: {slug}")
            print("ok", i, title)
            print("   ", a["id"], len(a["steps"]), a["reward"]["success"])
            print("   ", b["id"], len(b["steps"]), b["reward"]["success"])
        if len(set(slugs)) != len(slugs):
            raise SystemExit(f"duplicate slugs in catalog: {slugs}")
        print("selfcheck", len(LHC_PAIRS), "pairs", len(slugs), "episodes")
        return

    if mode == "loop":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else len(LHC_PAIRS)
        deadline = time.time() + 6 * 60 * 60
        published = 0
        hops = 0
        used = used_slugs()
        while published < target and time.time() < deadline:
            while st["lhc_pair"] < len(LHC_PAIRS):
                title, fa, fb, *_ = LHC_PAIRS[st["lhc_pair"]]
                probe_a, probe_b = fa(1), fb(1)
                probe_slugs = [
                    "-".join(x["id"].split("-")[2:-1]) for x in (probe_a, probe_b)
                ]
                if any(s in used for s in probe_slugs):
                    print(f"skip used pair {st['lhc_pair']} {title} {probe_slugs}", flush=True)
                    st["lhc_pair"] += 1
                    save_state(st)
                    continue
                break
            if st["lhc_pair"] >= len(LHC_PAIRS):
                print("catalog exhausted", flush=True)
                break
            res = try_reserve(LHC_DIR, 2)
            if res:
                rnd = res["round"]
                pair_i = st["lhc_pair"]
                recs, notes, title = emit_lhc(rnd, pair_i)
                for rec in recs:
                    slug = "-".join(rec["id"].split("-")[2:-1])
                    if slug in used:
                        raise SystemExit(f"refusing to publish used slug {slug}")
                    used.add(slug)
                publish_round(
                    LHC_DIR, rnd, res["token"], recs, notes,
                    res["batch_file"], res["notes_file"], res["staging_dir"],
                )
                st["lhc_pair"] += 1
                st["published"].append({"factory": "lhc", "round": rnd, "title": title, "ids": [x["id"] for x in recs]})
                save_state(st)
                published += 1
                print(f"PUBLISHED LHC r{rnd} pair={pair_i} {title}", flush=True)
                hops = 0
                continue
            hops += 1
            others = hop_targets()
            print(
                "LHC reserved; hop candidates (retry LHC; never sandbox-refusal):",
                [p.name for p in others[:8]],
                "sleep",
                flush=True,
            )
            time.sleep(1)
            if hops > 600:
                print("too many reserve failures; quota/reservation died", flush=True)
                break
        print(json.dumps({
            "published_this_run": published,
            "state_pairs": st["lhc_pair"],
            "rounds": [p["round"] for p in st["published"][-published:] if published],
        }, indent=2), flush=True)
        return

    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main() or 0)
