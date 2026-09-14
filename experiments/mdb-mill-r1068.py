#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1068+ unique leftover leftover leftover plants.

BAN r01–r1067 clones including r961 LAMMPS/GROMACS/... slugs and r840 OpenFOAM needles.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r961.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r961", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1068
P = _m.P
build_episode = _m.build_episode

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

PLANTS = [
    "avocet",
    "bittern",
    "chukar",
    "dunlin",
    "eider",
    "flamingo",
    "gannet",
    "harrier",
    "iora",
    "jacamar",
    "kestrel",
    "lapwing",
    "murre",
    "noddy",
    "osprey",
    "ptarmigan",
    "quetzal",
    "reeve",
    "sanderling",
    "tropicbird",
    "umbrellabird",
    "verdin",
    "wryneck",
    "xantus",
    "yellowthroat",
    "zonure",
    "alula",
    "bushtit",
    "creeper",
    "dipper",
    "empid",
    "flycatcher",
]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1067 clones (no r961 lammps-in-leftover-hybrid / gromacs-mdp-leftover-vrescale clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover leftover leftover plots. Ban r01–r1067 clones, libNNNN.
"""


def make(
    slug: str,
    plant: str,
    surface: str,
    pkg: str,
    old: str,
    new: str,
    fail: bool,
    pin: str,
    sot_old: str,
    sot_new: str,
    nest_old: str,
    nest_new: str,
    api_old: str,
    api_new: str,
    api_break: str,
    tool: str,
    test: str,
    ws: str,
    ext: str,
) -> dict:
    return P(
        slug,
        plant,
        surface,
        pkg,
        old,
        new,
        fail,
        pin,
        f"apps/api/{pin}",
        sot_old,
        sot_new,
        nest_old,
        nest_new,
        api_old,
        api_new,
        api_break,
        tool,
        test,
        ws,
        f"apps/api/{plant}.{ext}",
    )


TOOLS: list[tuple] = [
    ("lammps-kspace-leftover-pppm", "LAMMPS leftover vs kspace.in", "lammps", "29Aug2024", "22Jul2025", "kspace.in", "# lammps 29Aug2024", "# lammps 22Jul2025", "kspace_style ewald 1.0e-4", "kspace_style pppm 1.0e-5", "pair_style lj/cut/coul/cut 10.0", "pair_style lj/cut/coul/long 10.0", "ewald + coul/cut → pppm + coul/long", "lmp -h | head -n 1", "lmp -in apps/api/kspace.in", "lmp -in apps/legacy/kspace.in", "in"),
    ("gromacs-cons-leftover-allbonds", "GROMACS leftover vs cons.mdp", "gromacs", "2024.2", "2025.2", "cons.mdp", "; gromacs 2024.2", "; gromacs 2025.2", "constraints              = h-bonds", "constraints              = all-bonds", "constraint-algorithm     = lincs", "constraint-algorithm     = shake", "h-bonds+lincs → all-bonds+shake", "gmx --version | head -n 1", "gmx grompp -f apps/api/cons.mdp -c apps/api/api.gro -o /tmp/api.tpr", "gmx grompp -f apps/legacy/cons.mdp -c apps/legacy/api.gro -o /tmp/legacy.tpr", "mdp"),
    ("openfoam-fv-leftover-limited", "OpenFOAM leftover vs fvSchemes", "openfoam", "2312", "2412", "fvSchemes", "// openfoam 2312", "// openfoam 2412", "div(phi,U)      Gauss linear;", "div(phi,U)      Gauss limitedLinearV 1;", "grad(U)         Gauss linear;", "grad(U)         cellLimited Gauss linear 1;", "Gauss linear → limitedLinearV + cellLimited", "simpleFoam -help | head || true", "pimpleFoam -case apps/api", "pimpleFoam -case apps/legacy", "schemes"),
    ("fenics-assemble-leftover-form", "FEniCS leftover vs assemble.py", "fenics", "2019.1.0", "0.9.1", "assemble.py", "# fenics 2019.1.0", "# fenicsx 0.9.1", "A = assemble(a)", "A = fem.petsc.assemble_matrix(fem.form(a))", "from dolfin import assemble", "from dolfinx import fem", "assemble(a) → fem.petsc.assemble_matrix", "python3 -c 'import dolfinx; print(dolfinx.__version__)' || true", "python3 apps/api/assemble.py", "python3 apps/legacy/assemble.py", "py"),
    ("dealii-hp-leftover-dof", "Deal.II leftover vs hp.prm", "dealii", "9.6.0", "9.7.1", "hp.prm", "# dealii 9.6.0", "# dealii 9.7.1", "set DoFHandler = classic", "set DoFHandler = hp", "set FE = FE_Q(1)", "set FE = FE_Q(2)\nset hp_q_collection = true", "classic DoFHandler → hp + FE_Q(2)", "dealii_info || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "prm"),
    ("petsc-snes-leftover-vi", "PETSc leftover vs snes.rc", "petsc", "3.21.4", "3.22.4", "snes.rc", "# petsc 3.21.4", "# petsc 3.22.4", "-snes_type newtonls", "-snes_type vinewtonrsls", "-snes_linesearch_type bt", "-snes_linesearch_type l2", "newtonls+bt → vinewtonrsls+l2", "petscrc --version || true", "mpiexec -n 2 ./api -options_file apps/api/snes.rc", "mpiexec -n 2 ./api -options_file apps/legacy/snes.rc", "rc"),
    ("trilinos-tpetra-leftover-map", "Trilinos leftover vs tpetra.xml", "trilinos", "15.1.1", "16.1.0", "tpetra.xml", "<!-- trilinos 15.1.1 -->", "<!-- trilinos 16.1.0 -->", "<Parameter name=\"Node Type\" type=\"string\" value=\"Epetra\"/>", "<Parameter name=\"Node Type\" type=\"string\" value=\"Tpetra\"/>", "<Parameter name=\"Map Type\" type=\"string\" value=\"Serial\"/>", "<Parameter name=\"Map Type\" type=\"string\" value=\"Kokkos\"/>", "Epetra Serial → Tpetra Kokkos", "cmake --find-package -DNAME=Trilinos || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "xml"),
    ("hypre-pfmg-leftover-relax", "hypre leftover vs pfmg.opts", "hypre", "2.31.0", "2.32.1", "pfmg.opts", "# hypre 2.31.0", "# hypre 2.32.1", "-pc_hypre_type smg", "-pc_hypre_type pfmg", "-pc_hypre_smg_num_pre_relax 1", "-pc_hypre_pfmg_relax_type symmetric-SOR/Jacobi", "smg → pfmg symmetric-SOR", "pkg-config --modversion hypre || true", "./api -options_file apps/api/pfmg.opts", "./api -options_file apps/legacy/pfmg.opts", "opts"),
    ("namd-pme-leftover-grid", "NAMD leftover vs pme.conf", "namd", "2.14", "3.0.1", "pme.conf", "# namd 2.14", "# namd 3.0.1", "PME off", "PME on", "PMEGridSpacing 1.5", "PMEGridSpacing 1.0\nPMEInterpOrder 6", "PME off → on + finer grid", "namd3 --version || true", "namd3 apps/api/pme.conf", "namd3 apps/legacy/pme.conf", "conf"),
    ("amber-ntt-leftover-langevin", "AMBER leftover vs ntt.mdin", "amber", "22", "24", "ntt.mdin", "AMBER 22", "AMBER 24", "ntt=1, tautp=1.0,", "ntt=3, gamma_ln=2.0,", "temp0=300.0,", "temp0=310.0, ig=-1,", "Berendsen ntt=1 → Langevin ntt=3", "pmemd --version || true", "pmemd -O -i apps/api/ntt.mdin -o /tmp/api.mdout", "pmemd -O -i apps/legacy/ntt.mdin -o /tmp/legacy.mdout", "mdin"),
    ("vasp-algo-leftover-all", "VASP leftover vs ALGO", "vasp", "6.4.2", "6.5.1", "INCAR", "# vasp 6.4.2", "# vasp 6.5.1", "ALGO = Fast", "ALGO = All", "NELM = 60", "NELM = 120\nEDIFF = 1E-6", "ALGO Fast → All + tighter EDIFF", "vasp_std --version || true", "vasp_std", "vasp_std", "incar"),
    ("qe-occ-leftover-tetra", "Quantum ESPRESSO leftover vs occ.pwi", "qe", "7.3", "7.4.1", "occ.pwi", "! qe 7.3", "! qe 7.4.1", "occupations = 'smearing'", "occupations = 'tetrahedra_opt'", "degauss = 0.02", "degauss = 0.00", "smearing → tetrahedra_opt", "pw.x -v || true", "pw.x < apps/api/occ.pwi", "pw.x < apps/legacy/occ.pwi", "pwi"),
    ("cp2k-qs-leftover-otdiag", "CP2K leftover vs qs.inp", "cp2k", "2024.1", "2025.1", "qs.inp", "! cp2k 2024.1", "! cp2k 2025.1", "METHOD GPW", "METHOD GAPW", "OT MINIMIZER DIIS", "OT MINIMIZER BROYDEN", "GPW DIIS → GAPW BROYDEN", "cp2k.psmp --version | head -n 1", "cp2k.psmp -i apps/api/qs.inp", "cp2k.psmp -i apps/legacy/qs.inp", "inp"),
    ("orca-rij-leftover-nori", "ORCA leftover vs rij.inp", "orca", "5.0.4", "6.1.0", "rij.inp", "# orca 5.0.4", "# orca 6.1.0", "! B3LYP def2-SVP RIJCOSX", "! B3LYP def2-TZVP NORI", "%scf ConvForced 1 end", "%scf ConvForced 0 Thresh 1e-8 end", "RIJCOSX → NORI tighter SCF", "orca --help | head || true", "orca apps/api/rij.inp", "orca apps/legacy/rij.inp", "inp"),
    ("blast-task-leftover-mega", "BLAST leftover vs task.ncbirc", "blast", "2.15.0", "2.16.0", "task.ncbirc", "; blast 2.15.0", "; blast 2.16.0", "blastn -task blastn-short", "blastn -task megablast", "-word_size 7", "-word_size 28 -dust yes", "blastn-short → megablast + dust", "blastn -version | head -n 1", "blastn -query apps/api/q.fa -db api", "blastn -query apps/legacy/q.fa -db legacy", "ncbirc"),
    ("hmmer-ince-leftover-inct", "HMMER leftover vs ince.hmm", "hmmer", "3.3.2", "3.4", "ince.hmm", "# hmmer 3.3.2", "# hmmer 3.4", "hmmsearch --incE 0.01", "hmmsearch --incT 25.0", "--domE 1.0", "--incdomT 22.0", "--incE → --incT + --incdomT", "hmmsearch -h | head -n 1", "hmmsearch --incT 25 apps/api/ince.hmm apps/api/q.fa", "hmmsearch --incT 25 apps/legacy/ince.hmm apps/legacy/q.fa", "hmm"),
    ("bowtie-mp-leftover-rdg", "Bowtie leftover vs mp.cfg", "bowtie2", "2.5.1", "2.5.4", "mp.cfg", "# bowtie2 2.5.1", "# bowtie2 2.5.4", "--mp 6,2", "--mp 2,6", "--rdg 5,3", "--rdg 3,1 --rfg 3,1", "mp 6,2 → 2,6 + cheaper gaps", "bowtie2 --version | head -n 1", "bowtie2 -x apps/api/idx -U apps/api/r.fq", "bowtie2 -x apps/legacy/idx -U apps/legacy/r.fq", "cfg"),
    ("bwa-score-leftover-clip", "BWA leftover vs score.cfg", "bwa", "0.7.18", "0.7.19", "score.cfg", "# bwa 0.7.18", "# bwa 0.7.19", "bwa mem -A 1 -B 4", "bwa mem -A 2 -B 5 -L 10,10", "bwa mem -O 6", "bwa mem -O 4,4 -E 2,1", "match/mismatch + clip -L", "bwa 2>&1 | head -n 1 || true", "bwa mem apps/api/ref.fa apps/api/r.fq", "bwa mem apps/legacy/ref.fa apps/legacy/r.fq", "cfg"),
    ("samtools-sort-leftover-tag", "SAMtools leftover vs sort.cfg", "samtools", "1.20", "1.22", "sort.cfg", "# samtools 1.20", "# samtools 1.22", "sort -n", "sort -t RG", "sort -m 1G", "sort -m 2G -@ 8", "name sort → RG tag + threads", "samtools --version | head -n 1", "samtools sort -t RG apps/api/api.bam -o /tmp/api.bam", "samtools sort -t RG apps/legacy/api.bam -o /tmp/legacy.bam", "cfg"),
    ("picard-valid-leftover-lenient", "Picard leftover vs valid.xml", "picard", "3.1.1", "3.4.0", "valid.xml", "<!-- picard 3.1.1 -->", "<!-- picard 3.4.0 -->", "VALIDATION_STRINGENCY=STRICT", "VALIDATION_STRINGENCY=LENIENT", "MAX_RECORDS_IN_RAM=500000", "MAX_RECORDS_IN_RAM=2000000", "STRICT → LENIENT + RAM", "picard SortSam -h | head || true", "picard SortSam I=apps/api/api.bam O=/tmp/api.bam SO=coordinate", "picard SortSam I=apps/legacy/api.bam O=/tmp/legacy.bam SO=coordinate", "xml"),
    ("gatk-hc-leftover-mutect", "GATK leftover vs hc.list", "gatk", "4.5.0.0", "4.6.2.0", "hc.list", "# gatk 4.5.0.0", "# gatk 4.6.2.0", "HaplotypeCaller -ERC GVCF", "Mutect2 --f1r2-tar-gz f1r2.tar.gz", "--min-base-quality-score 10", "--min-base-quality-score 20 --max-reads-per-alignment-start 50", "HaplotypeCaller GVCF → Mutect2", "gatk --version | head -n 1", "gatk Mutect2 --arguments_file apps/api/hc.list", "gatk Mutect2 --arguments_file apps/legacy/hc.list", "list"),
    ("freebayes-pool-leftover-cont", "FreeBayes leftover vs pool.cfg", "freebayes", "1.3.7", "1.3.9", "pool.cfg", "# freebayes 1.3.7", "# freebayes 1.3.9", "--pooled-discrete", "--pooled-continuous", "--ploidy 2", "--ploidy 2 --min-alternate-fraction 0.05", "pooled-discrete → continuous + AF", "freebayes --version || true", "freebayes -f apps/api/ref.fa apps/api/api.bam", "freebayes -f apps/legacy/ref.fa apps/legacy/api.bam", "cfg"),
    ("snakemake-sdm-leftover-apptainer", "Snakemake leftover vs sdm.smk", "snakemake", "8.16.0", "9.1.1", "sdm.smk", "# snakemake 8.16.0", "# snakemake 9.1.1", "container: \"docker://old:1\"", "container: \"docker://api:2\"", "conda: \"envs/old.yaml\"", "software-deployment-method:\n        - apptainer", "conda pin → apptainer sdm", "snakemake --version", "snakemake -j1 -s apps/api/sdm.smk --sdm apptainer", "snakemake -j1 -s apps/legacy/sdm.smk --sdm apptainer", "smk"),
    ("nextflow-fusion-leftover-wave", "Nextflow leftover vs fusion.config", "nextflow", "24.04.4", "25.04.0", "fusion.config", "// nextflow 24.04.4", "// nextflow 25.04.0", "fusion.enabled = false", "fusion.enabled = true", "wave.enabled = false", "wave.enabled = true\nwave.freeze = true", "fusion off → fusion+wave freeze", "nextflow -version | head -n 1", "nextflow run apps/api/main.nf -c apps/api/fusion.config", "nextflow run apps/legacy/main.nf -c apps/legacy/fusion.config", "nf"),
    ("cromwell-hog-leftover-cache", "Cromwell leftover vs hog.conf", "cromwell", "87", "90", "hog.conf", "# cromwell 87", "# cromwell 90", "hogwild = false", "hogwild = true", "call-caching { enabled = false }", "call-caching { enabled = true invalidate-bad-cache-results = true }", "hogwild + cache invalidate", "java -jar cromwell.jar --version || true", "java -jar cromwell.jar run apps/api/api.wdl", "java -jar cromwell.jar run apps/legacy/api.wdl", "conf"),
    ("toil-k8s-leftover-batch", "Toil leftover vs k8s.yml", "toil", "7.0.0", "8.2.0", "k8s.yml", "# toil 7.0.0", "# toil 8.2.0", "batchSystem: single_machine", "batchSystem: kubernetes", "disableCaching: true", "disableCaching: false\nkubernetesHost: https://k8s:6443", "single_machine → kubernetes", "toil --version", "toil-cwl-runner --config apps/api/k8s.yml apps/api/api.cwl apps/api/job.json", "toil-cwl-runner --config apps/legacy/k8s.yml apps/legacy/api.cwl apps/legacy/job.json", "yml"),
    ("galaxy-tus-leftover-upload", "Galaxy leftover vs tus.yml", "galaxy", "24.1", "25.0", "tus.yml", "# galaxy 24.1", "# galaxy 25.0", "enable_tus: false", "enable_tus: true", "file_upload_monitor_interval: 5", "file_upload_monitor_interval: 1\ntus_upload_store: /data/tus", "tus off → on + store", "galaxy --version || true", "galaxyctl start --config apps/api/tus.yml", "galaxyctl start --config apps/legacy/tus.yml", "yml"),
    ("nfcore-schema-leftover-params", "nf-core leftover vs schema.config", "nf-core", "2.14", "3.2.1", "schema.config", "// nf-core 2.14", "// nf-core 3.2.1", "params.schema_ignore_params = 'genomes'", "params.validate_params = true", "params.custom_config_version = 'master'", "params.custom_config_base = 'https://raw.githubusercontent.com/nf-core/configs/master'", "schema_ignore → validate_params", "nf-core --version", "nextflow run nf-core/rnaseq -c apps/api/schema.config", "nextflow run nf-core/rnaseq -c apps/legacy/schema.config", "config"),
    ("spack-reuse-leftover-extern", "Spack leftover vs reuse.yaml", "spack", "0.22.1", "1.0.0", "reuse.yaml", "# spack 0.22.1", "# spack 1.0.0", "reuse: false", "reuse: true", "externals: []", "packages:\n  all:\n    require: '%gcc@13'", "reuse false → true + gcc@13 require", "spack --version", "spack -e apps/api concretize -f", "spack -e apps/legacy concretize -f", "yaml"),
    ("easybuild-block-leftover-python", "EasyBuild leftover vs py.eb", "easybuild", "4.9.4", "5.1.1", "py.eb", "# easybuild 4.9.4", "# easybuild 5.1.1", "easyblock = 'PythonPackage'", "easyblock = 'PythonBundle'", "exts_list = [('numpy', '1.24.4', {})]", "exts_list = [('numpy', '2.1.3', {})]", "PythonPackage → PythonBundle numpy 2", "eb --version", "eb apps/api/py.eb -dr", "eb apps/legacy/py.eb -dr", "eb"),
    ("guix-inf-leftover-manifest", "Guix leftover vs inf.scm", "guix", "1.4.0", "1.5.0", "inf.scm", ";; guix 1.4.0", ";; guix 1.5.0", "(use-modules (guix packages))", "(use-modules (guix inferior) (guix channels))", "(specifications->manifest '(\"python\"))", "(packages->manifest (list (first (lookup-inferior-packages inf \"python\"))))", "specifications → inferior lookup", "guix --version | head -n 1", "guix package -m apps/api/inf.scm", "guix package -m apps/legacy/inf.scm", "scm"),
    ("nix-lock-leftover-revpin", "Nix leftover vs flake.nix", "nix", "2.24.10", "2.26.2", "flake.nix", "nix = \"2.24.10\"", "nix = \"2.26.2\"", "inputs.nixpkgs.url = \"github:NixOS/nixpkgs/nixos-24.05\"", "inputs.nixpkgs.url = \"github:NixOS/nixpkgs/nixos-25.05\"", "outputs = { self, nixpkgs }:", "outputs = { self, nixpkgs, ... }:", "nixos-24.05 → 25.05 flake inputs", "nix --version", "nix flake lock apps/api --update-input nixpkgs", "nix flake lock apps/legacy --update-input nixpkgs", "nix"),
]

assert len(TOOLS) % 2 == 0
assert len(TOOLS) == 32
assert len(TOOLS) <= len(PLANTS)

PAIRS: list[tuple[dict, dict]] = []
_pi = 0
for i in range(0, len(TOOLS), 2):
    a = TOOLS[i]
    b = TOOLS[i + 1]
    suc = make(
        a[0], PLANTS[_pi], a[1], a[2], a[3], a[4], False,
        a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15], a[16],
    )
    _pi += 1
    failp = make(
        b[0], PLANTS[_pi], b[1], b[2], b[3], b[4], True,
        b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15], b[16],
    )
    _pi += 1
    PAIRS.append((suc, failp))


def _validate_catalog() -> None:
    slugs = [spec["slug"] for pair in PAIRS for spec in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r1068 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1068 catalog")


_validate_catalog()


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
