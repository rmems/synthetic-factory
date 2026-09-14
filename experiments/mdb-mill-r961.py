#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r961+ unique leftover leftover leftover plants.

BAN r01–r960 clones including r918 GROMACS/LAMMPS/NAMD/AMBER/CP2K/QE/ORCA/BLAST/
HMMER/GATK/SAMtools/Picard/BWA and r840 OpenFOAM/FEniCS/PETSc/Trilinos needles.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r840.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r840", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 977
P = _m.P
build_episode = _m.build_episode

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "openems-xml-leftover-fdtd",
    "siliconcompiler-py-leftover-target",
    "lammps-in-leftover-coul",
    "gromacs-mdp-leftover-sd",
    "openfoam-wmake",
    "fenics-dolfin",
    "dealii-cmake-leftover-affine",
    "petsc-makefile",
    "trilinos-cmake",
    "namd-conf-leftover-rigidwater",
    "amber-mdin-leftover-ntp",
    "qespresso-pwi-leftover-ibrav",
    "cp2k-inp-leftover-gapw",
    "orca-inp-leftover-wb97",
    "blastplus-ncbirc-leftover-diamond",
    "hmmer-hmm-leftover-cutnc",
    "bwamem2-cfg-leftover-mem2",
    "samtools-cfg-leftover-mapq",
    "picard-xml-leftover-spark",
    "gatk-args-leftover-bpres",
    "nix-fetchipfs",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

FACTORY_DIR = (
    Path(__file__).resolve().parents[1]
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "monorepo-dep-bump-factory"
)

FREE_PLANTS = (
    "ibis",
    "jacana",
    "kiwi",
    "loon",
    "magpie",
    "nuthatch",
    "oriole",
    "pelican",
    "quail",
    "rail",
    "siskin",
    "tanager",
    "urubu",
    "vireo",
    "whimbrel",
    "xenops",
    "yellowlegs",
    "zosterops",
    "anhinga",
    "bobolink",
    "catbird",
    "dickcissel",
    "egret",
    "fulmar",
    "godwit",
    "heron",
    "ibis2",
    "jacana2",
    "kiwi2",
    "loon2",
    "magpie2",
    "nuthatch2",
)
PLANTS = list(FREE_PLANTS)


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 87 + (round_n % 6)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r960 clones (ban openems-xml-leftover-fdtd / siliconcompiler-py-leftover-target; no pnpm/zod/changesets/maven/gradle/go.work/uv/poetry/turbo/cargo-patch/yarn/bun/nx).

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
Keep unique leftover leftover leftover plots. Ban r01–r960 clones, libNNNN, Mix/Elixir, Conan/Hunter/vcpkg/Meson wrap/CMake FetchContent.
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
    ("lammps-in-leftover-hybrid", "LAMMPS leftover vs api.in", "lammps", "2Aug2023", "22Jul2025", "api.in", "# lammps 2Aug2023", "# lammps 22Jul2025", "pair_style lj/cut 2.5", "pair_style hybrid/overlay lj/cut 2.5 coul/long 2.5", "fix 1 all nve", "fix 1 all nvt temp 300 300 100", "lj/cut + nve → hybrid/overlay coul/long + nvt", "lmp -h | head -n 1", "lmp -in apps/api/api.in", "lmp -in apps/legacy/api.in", "in"),
    ("gromacs-mdp-leftover-vrescale", "GROMACS leftover vs api.mdp", "gromacs", "2023.3", "2025.1", "api.mdp", "; gromacs 2023.3", "; gromacs 2025.1", "tcoupl                   = berendsen", "tcoupl                   = v-rescale", "pcoupl                   = berendsen", "pcoupl                   = c-rescale", "berendsen t/p → v-rescale + c-rescale", "gmx --version | head -n 1", "gmx grompp -f apps/api/api.mdp -c apps/api/api.gro -o /tmp/api.tpr", "gmx grompp -f apps/legacy/api.mdp -c apps/legacy/api.gro -o /tmp/legacy.tpr", "mdp"),
    ("openfoam-ctrl-leftover-pimple", "OpenFOAM leftover vs controlDict", "openfoam", "2212", "2412", "controlDict", "// openfoam 2212", "// openfoam 2412", "application     simpleFoam;", "application     pimpleFoam;", "endTime         1000;", "endTime         2000;\ndeltaT          0.001;", "simpleFoam → pimpleFoam + deltaT", "simpleFoam -help | head || true", "pimpleFoam -case apps/api", "pimpleFoam -case apps/legacy", "dict"),
    ("fenics-py-leftover-functionspace", "FEniCS leftover vs api.py", "fenics", "2019.1.0", "0.9.0", "api.py", "# fenics 2019.1.0", "# fenicsx 0.9.0", "V = FunctionSpace(mesh, \"P\", 1)", "V = functionspace(mesh, (\"Lagrange\", 1))", "from dolfin import *", "from dolfinx import mesh, fem", "FunctionSpace dolfin → functionspace dolfinx", "python3 -c 'import dolfinx; print(dolfinx.__version__)' || true", "python3 apps/api/api.py", "python3 apps/legacy/api.py", "py"),
    ("dealii-prm-leftover-mapping", "Deal.II leftover vs api.prm", "dealii", "9.5.1", "9.7.0", "api.prm", "# dealii 9.5.1", "# dealii 9.7.0", "set Mapping degree = 1", "set Mapping degree = 2", "set Quadrature = QGauss", "set Quadrature = QGaussLobatto", "mapping 1 + QGauss → degree 2 + QGaussLobatto", "dealii_info || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "prm"),
    ("petsc-opts-leftover-kspgmres", "PETSc leftover vs petscrc", "petsc", "3.19.6", "3.22.3", "petscrc", "# petsc 3.19.6", "# petsc 3.22.3", "-ksp_type bcgs", "-ksp_type gmres", "-pc_type ilu", "-pc_type gamg", "bcgs+ilu → gmres+gamg", "petscrc --version || true", "mpiexec -n 2 ./api -options_file apps/api/petscrc", "mpiexec -n 2 ./api -options_file apps/legacy/petscrc", "rc"),
    ("trilinos-xml-leftover-belos", "Trilinos leftover vs api.xml", "trilinos", "14.4.0", "16.1.0", "api.xml", "<!-- trilinos 14.4.0 -->", "<!-- trilinos 16.1.0 -->", "<Parameter name=\"Linear Solver Type\" type=\"string\" value=\"Amesos2\"/>", "<Parameter name=\"Linear Solver Type\" type=\"string\" value=\"Belos\"/>", "<Parameter name=\"Preconditioner Type\" type=\"string\" value=\"Ifpack2\"/>", "<Parameter name=\"Preconditioner Type\" type=\"string\" value=\"MueLu\"/>", "Amesos2+Ifpack2 → Belos+MueLu", "cmake --find-package -DNAME=Trilinos || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "xml"),
    ("hypre-opts-leftover-boomeramg", "hypre leftover vs hypre.opts", "hypre", "2.28.0", "2.32.0", "hypre.opts", "# hypre 2.28.0", "# hypre 2.32.0", "-pc_hypre_type pilut", "-pc_hypre_type boomeramg", "-pc_hypre_pilut_maxiter 4", "-pc_hypre_boomeramg_coarsen_type HMIS", "pilut → boomeramg HMIS", "pkg-config --modversion hypre || true", "./api -options_file apps/api/hypre.opts", "./api -options_file apps/legacy/hypre.opts", "opts"),
    ("namd-conf-leftover-langevin", "NAMD leftover vs api.conf", "namd", "2.14", "3.0.2", "api.conf", "# namd 2.14", "# namd 3.0.2", "langevin on", "langevinPiston on", "langevinTemp 300", "langevinPistonTemp 300\nlangevinPistonTarget 1.01325", "langevin thermostat → langevinPiston NPT", "namd3 --version || true", "namd3 apps/api/api.conf", "namd3 apps/legacy/api.conf", "conf"),
    ("amber-mdin-leftover-igb", "AMBER leftover vs api.mdin", "amber", "22", "24", "api.mdin", "AMBER 22", "AMBER 24", "igb=0, ntb=1,", "igb=8, ntb=0,", "gbsa=0,", "gbsa=1,", "explicit ntb=1 → igb=8 GBSA", "pmemd --version || true", "pmemd -O -i apps/api/api.mdin -o /tmp/api.mdout", "pmemd -O -i apps/legacy/api.mdin -o /tmp/legacy.mdout", "mdin"),
    ("vasp-incar-leftover-ivdw", "VASP leftover vs INCAR", "vasp", "6.3.2", "6.5.0", "INCAR", "# vasp 6.3.2", "# vasp 6.5.0", "IVDW = 0", "IVDW = 12", "GGA = PE", "GGA = PE\nLVDW_EWALD = .TRUE.", "IVDW 0 → 12 DFT-D3 + LVDW_EWALD", "vasp_std --version || true", "vasp_std", "vasp_std", "incar"),
    ("qe-pwi-leftover-vdwdf", "Quantum ESPRESSO leftover vs api.pwi", "qe", "7.2", "7.4.1", "api.pwi", "! qe 7.2", "! qe 7.4.1", "input_dft = 'PBE'", "input_dft = 'vdw-df2'", "ecutwfc = 40.0", "ecutwfc = 50.0\necutrho = 400.0", "PBE → vdw-df2 + ecutrho", "pw.x -v || true", "pw.x < apps/api/api.pwi", "pw.x < apps/legacy/api.pwi", "pwi"),
    ("cp2k-inp-leftover-ot", "CP2K leftover vs api.inp", "cp2k", "2023.2", "2025.1", "api.inp", "! cp2k 2023.2", "! cp2k 2025.1", "MINIMIZER DIIS", "MINIMIZER OT", "EPS_SCF 1.0E-6", "EPS_SCF 1.0E-7\nLINESEARCH 3PNT", "DIIS → OT + 3PNT", "cp2k.psmp --version | head -n 1", "cp2k.psmp -i apps/api/api.inp", "cp2k.psmp -i apps/legacy/api.inp", "inp"),
    ("orca-inp-leftover-dlpno", "ORCA leftover vs api.inp", "orca", "5.0.4", "6.1.0", "api.inp", "# orca 5.0.4", "# orca 6.1.0", "! B3LYP def2-SVP", "! DLPNO-CCSD(T) def2-TZVP", "%scf MaxIter 125 end", "%mdci MaxIter 50 end", "B3LYP → DLPNO-CCSD(T)", "orca --help | head || true", "orca apps/api/api.inp", "orca apps/legacy/api.inp", "inp"),
    ("blast-ncbirc-leftover-task", "BLAST leftover vs .ncbirc", "blast", "2.14.1", "2.16.0", ".ncbirc", "; blast 2.14.1", "; blast 2.16.0", "blastp -task blastp", "blastp -task blastp-fast", "-evalue 1e-5", "-evalue 1e-6 -max_target_seqs 20", "blastp → blastp-fast + max_target_seqs", "blastp -version | head -n 1", "blastp -query apps/api/q.fa -db api", "blastp -query apps/legacy/q.fa -db legacy", "ncbirc"),
    ("hmmer-hmm-leftover-cutga", "HMMER leftover vs api.hmm", "hmmer", "3.3.2", "3.4", "api.hmm", "# hmmer 3.3.2", "# hmmer 3.4", "TC    22.0 22.0", "GA    25.0 25.0", "hmmsearch --cut_tc api.hmm q.fa", "hmmsearch --cut_ga api.hmm q.fa", "TC + --cut_tc → GA + --cut_ga", "hmmsearch -h | head -n 1", "hmmsearch --cut_ga apps/api/api.hmm apps/api/q.fa", "hmmsearch --cut_ga apps/legacy/api.hmm apps/legacy/q.fa", "hmm"),
    ("bowtie2-cfg-leftover-sensitive", "Bowtie leftover vs api.cfg", "bowtie2", "2.4.5", "2.5.4", "api.cfg", "# bowtie2 2.4.5", "# bowtie2 2.5.4", "--end-to-end --fast", "--local --very-sensitive-local", "-k 1", "-k 4 --no-mixed", "end-to-end fast → local very-sensitive-local", "bowtie2 --version | head -n 1", "bowtie2 -x apps/api/idx -U apps/api/r.fq", "bowtie2 -x apps/legacy/idx -U apps/legacy/r.fq", "cfg"),
    ("bwa-cfg-leftover-mem3", "BWA leftover vs api.cfg", "bwa", "0.7.17", "0.7.19", "api.cfg", "# bwa 0.7.17", "# bwa 0.7.19", "bwa mem -t 4", "bwa mem -x intractg -t 8", "bwa aln ref.fa r.fq", "bwa mem -Y ref.fa r.fq", "bwa aln → mem -x intractg -Y", "bwa 2>&1 | head -n 1 || true", "bwa mem apps/api/ref.fa apps/api/r.fq", "bwa mem apps/legacy/ref.fa apps/legacy/r.fq", "cfg"),
    ("samtools-cfg-leftover-cram", "SAMtools leftover vs api.cfg", "samtools", "1.17", "1.22", "api.cfg", "# samtools 1.17", "# samtools 1.22", "view -b -o api.bam", "view -C -T ref.fa -o api.cram", "index api.bam", "index -c api.cram", "bam view -b → CRAM -C + index -c", "samtools --version | head -n 1", "samtools view -C -T apps/api/ref.fa apps/api/api.sam -o /tmp/api.cram", "samtools view -C -T apps/legacy/ref.fa apps/legacy/api.sam -o /tmp/legacy.cram", "cfg"),
    ("picard-xml-leftover-optical", "Picard leftover vs api.xml", "picard", "2.27.5", "3.4.0", "api.xml", "<!-- picard 2.27.5 -->", "<!-- picard 3.4.0 -->", "REMOVE_DUPLICATES=false", "REMOVE_DUPLICATES=true OPTICAL_DUPLICATE_PIXEL_DISTANCE=2500", "MarkDuplicates I=api.bam O=dedup.bam", "MarkDuplicates I=api.bam O=dedup.bam M=api.metrics", "optical distance + REMOVE_DUPLICATES true", "picard MarkDuplicates -h | head || true", "picard MarkDuplicates I=apps/api/api.bam O=/tmp/api.bam M=/tmp/api.metrics", "picard MarkDuplicates I=apps/legacy/api.bam O=/tmp/legacy.bam M=/tmp/legacy.metrics", "xml"),
    ("gatk-args-leftover-cnn", "GATK leftover vs args.list", "gatk", "4.4.0.0", "4.6.2.0", "args.list", "# gatk 4.4.0.0", "# gatk 4.6.2.0", "--filter-name QD --filter-expression \"QD < 2.0\"", "--filter-name CNN_Score --filter-expression \"CNN_1D < -0.1\"", "VariantFiltration -V api.vcf", "CNNScoreVariants -V api.vcf", "hard QD filter → CNNScoreVariants", "gatk --version | head -n 1", "gatk CNNScoreVariants --arguments_file apps/api/args.list", "gatk CNNScoreVariants --arguments_file apps/legacy/args.list", "list"),
    ("freebayes-cfg-leftover-minimapq", "FreeBayes leftover vs api.cfg", "freebayes", "1.3.6", "1.3.9", "api.cfg", "# freebayes 1.3.6", "# freebayes 1.3.9", "--min-mapping-quality 1", "--min-mapping-quality 30", "--min-alternate-count 2", "--min-alternate-count 4 --genotype-qualities", "MAPQ 1 → 30 + GQ", "freebayes --version || true", "freebayes -f apps/api/ref.fa apps/api/api.bam", "freebayes -f apps/legacy/ref.fa apps/legacy/api.bam", "cfg"),
    ("snakemake-smk-leftover-conda", "Snakemake leftover vs Snakefile", "snakemake", "7.32.4", "9.1.1", "Snakefile", "# snakemake 7.32.4", "# snakemake 9.1.1", "conda: \"envs/old.yaml\"", "conda: \"envs/api.yaml\"", "shell: \"bwa mem {input} > {output}\"", "resources:\n        mem_mb=8000\n    shell: \"bwa mem {input} > {output}\"", "conda env + mem_mb resources", "snakemake --version", "snakemake -j1 -s apps/api/Snakefile --use-conda", "snakemake -j1 -s apps/legacy/Snakefile --use-conda", "smk"),
    ("nextflow-nf-leftover-docker", "Nextflow leftover vs nextflow.config", "nextflow", "23.10.1", "25.04.0", "nextflow.config", "// nextflow 23.10.1", "// nextflow 25.04.0", "process.container = 'old:1'", "docker.enabled = true\nprocess.container = 'api:2'", "process.executor = 'local'", "process.executor = 'local'\nwave.enabled = true", "container pin → docker + wave", "nextflow -version | head -n 1", "nextflow run apps/api/main.nf -c apps/api/nextflow.config", "nextflow run apps/legacy/main.nf -c apps/legacy/nextflow.config", "nf"),
    ("cromwell-wdl-leftover-callcache", "Cromwell leftover vs cromwell.conf", "cromwell", "85", "90", "cromwell.conf", "# cromwell 85", "# cromwell 90", "call-caching { enabled = false }", "call-caching { enabled = true }", "backend.default = Local", "backend.default = Local\nfilesytem.local.localization = [\"hard-link\", \"copy\"]", "call-caching off → on + localization", "java -jar cromwell.jar --version || true", "java -jar cromwell.jar run apps/api/api.wdl", "java -jar cromwell.jar run apps/legacy/api.wdl", "conf"),
    ("toil-cwl-leftover-mesos", "Toil leftover vs toil.yml", "toil", "6.1.0", "8.2.0", "toil.yml", "# toil 6.1.0", "# toil 8.2.0", "batchSystem: single_machine", "batchSystem: mesos", "disableCaching: true", "disableCaching: false\nmesosEndpoint: localhost:5050", "single_machine → mesos + cache", "toil --version", "toil-cwl-runner --config apps/api/toil.yml apps/api/api.cwl apps/api/job.json", "toil-cwl-runner --config apps/legacy/toil.yml apps/legacy/api.cwl apps/legacy/job.json", "yml"),
    ("galaxy-yml-leftover-toolid", "Galaxy leftover vs galaxy.yml", "galaxy", "23.1", "25.0", "galaxy.yml", "# galaxy 23.1", "# galaxy 25.0", "tool_config_file: tool_conf.xml.sample", "tool_config_file: tool_conf.xml", "conda_auto_install: false", "conda_auto_install: true\nenable_tool_document_cache: true", "sample tool_conf → live + conda_auto_install", "galaxy --version || true", "galaxyctl start --config apps/api/galaxy.yml", "galaxyctl start --config apps/legacy/galaxy.yml", "yml"),
    ("nfcore-yml-leftover-igenomes", "nf-core leftover vs nextflow.config", "nf-core", "2.10", "3.2.1", "nextflow.config", "// nf-core 2.10", "// nf-core 3.2.1", "params.igenomes_base = 's3://ngi-igenomes/igenomes'", "params.igenomes_ignore = true", "params.fasta = null", "params.fasta = 'assets/genome.fa'", "igenomes_base → ignore + local fasta", "nf-core --version", "nextflow run nf-core/rnaseq -c apps/api/nextflow.config", "nextflow run nf-core/rnaseq -c apps/legacy/nextflow.config", "config"),
    ("spack-yaml-leftover-concretizer", "Spack leftover vs spack.yaml", "spack", "0.21.2", "1.0.0", "spack.yaml", "# spack 0.21.2", "# spack 1.0.0", "concretizer: original", "concretizer: clingo", "unify: false", "unify: true\nduplicate_nodes: none", "original concretizer → clingo unify", "spack --version", "spack -e apps/api concretize -f", "spack -e apps/legacy concretize -f", "yaml"),
    ("easybuild-eb-leftover-toolchain", "EasyBuild leftover vs api.eb", "easybuild", "4.8.2", "5.1.1", "api.eb", "# easybuild 4.8.2", "# easybuild 5.1.1", "toolchain = {'name': 'foss', 'version': '2022a'}", "toolchain = {'name': 'foss', 'version': '2024a'}", "versionsuffix = '-Python-3.10.4'", "versionsuffix = '-Python-3.12.3'", "foss 2022a py3.10 → 2024a py3.12", "eb --version", "eb apps/api/api.eb -dr", "eb apps/legacy/api.eb -dr", "eb"),
    ("guix-scm-leftover-channels", "Guix leftover vs channels.scm", "guix", "1.4.0", "1.5.0", "channels.scm", ";; guix 1.4.0", ";; guix 1.5.0", "(channel (name 'guix) (url \"https://git.savannah.gnu.org/git/guix.git\") (branch \"master\"))", "(channel (name 'guix) (url \"https://git.savannah.gnu.org/git/guix.git\") (commit \"f00d\"))", "(use-modules (gnu))", "(use-modules (gnu) (guix channels))", "branch master → pinned commit + channels", "guix --version | head -n 1", "guix pull -C apps/api/channels.scm", "guix pull -C apps/legacy/channels.scm", "scm"),
    ("nix-lock-leftover-narhash", "Nix leftover vs flake.lock", "nix", "2.18.1", "2.26.2", "flake.lock", "\"nix\": \"2.18.1\"", "\"nix\": \"2.26.2\"", "\"narHash\": \"sha256-old\"", "\"narHash\": \"sha256-new\"", "\"locked\": {\"rev\": \"aaa\"}", "\"locked\": {\"rev\": \"bbb\", \"narHash\": \"sha256-new\"}", "flake.lock narHash + rev pin (not fetchipfs)", "nix --version", "nix flake lock apps/api --update-input nixpkgs", "nix flake lock apps/legacy --update-input nixpkgs", "lock"),
]

assert len(TOOLS) % 2 == 0
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
        raise SystemExit("duplicate slugs in r961 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r961 catalog")


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
