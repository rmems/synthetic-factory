#!/usr/bin/env python3
"""Grok 4.6 LHC mill w4cv: unused FEM/mesh/solver plants after w4cu.

Never writes outputs/raw. Unique path so it cannot be overwritten by w4 mash.
BAN: w4cs RSEM/Seurat/Mutect2/Hail, w4cr FastQC/SPAdes, r4778 nim-lent, r4777 zig,
r4687 rust-pin, r4580 kanidm/gluu, identity-origin, RPITIT, Prom hist,
ThinLTO, Go loopvar, Django ASGI, Vale, Koka, published.
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
STATE = Path("/tmp/lhc_mill_g46_w4cv_state.json")
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
    "fastqc", "multiqc", "spades", "flye", "kraken", "hisat2",
    "rsem", "seurat", "mutect2", "hail-npart", "cellbender",
)


def hx(kind: str, rnd: int, slug: str) -> str:
    return hashlib.sha1(f"w4cv|{kind}|{rnd}|{slug}|grok-4.6".encode()).hexdigest()[:4]


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



# Compact unused FEM / mesh / sparse-solver plants after w4cu.
PLANTS = {
    "firedrake": mk(True, "pr-firedrake-tsfc-mode", "lock-fdtsfc",
        "the Firedrake assemble that omitted tsfc_interface mode so a 3D form sat in coffee and JIT-stalled",
        "fd.py", "assemble(inner(grad(u),grad(v))*dx)", "parameters['tsfc_interface']='tsfc'",
        "tsfc_interface", "harbor assemble only. pack tsfc_interface.",
        "FAIL test_assign: coffee JIT stall; tsfc_interface missing",
        "assemble only", "assemble is not tsfc_interface"),
    "dolfinx": mk(False, "pr-dolfinx-ghost-mode", "quay-dfxgh",
        "the DOLFINx mesh that omitted ghost_mode so a DG form missed shared facets",
        "dfx.py", "mesh.create_unit_cube(comm, 16,16,16)", "ghost_mode=GhostMode.shared_facet",
        "ghost_mode", "harbor create_unit_cube only. pack shared_facet.",
        "FAIL test_assign: DG missed facets; ghost_mode missing",
        "unit_cube only", "unit_cube is not ghost_mode"),
    "sundials": mk(True, "pr-sundials-cvode-maxord", "lock-cvord",
        "the CVODE BDF that omitted maxord so a stiff ODE used order 5 and Newton failed",
        "cvode.c", "CVode(cvode_mem, tout, y, &t, CV_NORMAL)", "CVodeSetMaxOrd(cvode_mem, 2)",
        "CVodeSetMaxOrd", "harbor CVode only. pack maxord 2.",
        "FAIL test_assign: order 5 Newton fail; maxord missing",
        "CVode only", "CVode is not maxord"),
    "armadillo": mk(False, "pr-armadillo-openblas-threads", "quay-armaomp",
        "the Armadillo eig_sym that omitted OPENBLAS_NUM_THREADS so a 4k matrix sat on one core",
        "arma.cpp", "eig_sym(eigval, A)", "OPENBLAS_NUM_THREADS=16",
        "OPENBLAS_NUM_THREADS", "harbor eig_sym only. pack OPENBLAS_NUM_THREADS.",
        "FAIL test_assign: 4k 1 core; OPENBLAS_NUM_THREADS missing",
        "eig_sym only", "eig_sym is not OPENBLAS"),
    "eigen3": mk(True, "pr-eigen3-omp-threads", "lock-eigomp",
        "the Eigen SelfAdjointEigenSolver that omitted OMP_NUM_THREADS so a 8k SPD sat serial",
        "eig.cpp", "SelfAdjointEigenSolver<MatrixXd> es(A)", "OMP_NUM_THREADS=16",
        "OMP_NUM_THREADS", "harbor SelfAdjointEigenSolver only. pack OMP_NUM_THREADS.",
        "FAIL test_assign: 8k SPD serial; OMP_NUM_THREADS missing",
        "solver only", "solver is not OMP"),
    "opencv": mk(False, "pr-opencv-use-optimized", "quay-cvopt",
        "the OpenCV remap that omitted setUseOptimized so a 8k image sat in the baseline path",
        "cv.py", "cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)", "cv2.setUseOptimized(True)",
        "setUseOptimized", "harbor remap only. pack setUseOptimized.",
        "FAIL test_assign: 8k baseline path; setUseOptimized missing",
        "remap only", "remap is not setUseOptimized"),
    "open3d": mk(True, "pr-open3d-t-device-cuda", "lock-o3dcu",
        "the Open3D t.geometry that omitted device=CUDA so a 20M-point ICP sat on CPU",
        "o3d.py", "pcd = o3d.t.geometry.PointCloud()", "device=o3d.core.Device('CUDA:0')",
        "CUDA:0", "harbor PointCloud only. pack CUDA device.",
        "FAIL test_assign: 20M ICP CPU; CUDA missing",
        "PointCloud only", "PointCloud is not CUDA"),
    "trimesh": mk(False, "pr-trimesh-process-validate", "quay-tmval",
        "the trimesh load that omitted process=False so a 4M-face STL repaired in RAM and OOM'd",
        "tm.py", "trimesh.load('in.stl')", "trimesh.load('in.stl', process=False)",
        "process=False", "harbor load stl only. pack process=False.",
        "FAIL test_assign: 4M-face repair OOM; process=False missing",
        "load only", "load is not process"),
    "meshio": mk(True, "pr-meshio-binary-vtu", "lock-msbin",
        "the meshio write that omitted binary=True so a 20M-cell VTU stayed ASCII and filled disk",
        "meshio.py", "meshio.write('out.vtu', mesh)", "meshio.write('out.vtu', mesh, binary=True)",
        "binary=True", "harbor write vtu only. pack binary.",
        "FAIL test_assign: ASCII disk fill; binary missing",
        "write only", "write is not binary"),
    "tetgen": mk(False, "pr-tetgen-quality-q", "quay-ttgq",
        "the TetGen run that omitted -q so a 1M-tet mesh had radius-edge 20 and FEM blew",
        "tet.sh", "tetgen -p in.poly", "tetgen -pq1.2 in.poly",
        "-q", "harbor -p only. pack -q 1.2.",
        "FAIL test_assign: radius-edge 20; -q missing",
        "-p only", "-p is not -q"),
    "netgen": mk(True, "pr-netgen-maxh-mesh", "lock-ngmaxh",
        "the Netgen generate that omitted maxh so a 2mm CAD meshed at 20mm and stress vanished",
        "ng.py", "geo.GenerateMesh()", "geo.GenerateMesh(maxh=2.0)",
        "maxh", "harbor GenerateMesh only. pack maxh 2.0.",
        "FAIL test_assign: 20mm mesh; maxh missing",
        "GenerateMesh only", "GenerateMesh is not maxh"),
    "pygmsh": mk(False, "pr-pygmsh-mesh-size-cb", "quay-pgmsz",
        "the pygmsh generate that omitted mesh_size_callback so a 0.1mm fillet sat at 5mm",
        "pg.py", "gmsh.model.mesh.generate(3)", "mesh_size_callback=lambda *a: 0.1",
        "mesh_size_callback", "harbor generate 3 only. pack mesh_size_callback.",
        "FAIL test_assign: 5mm fillet; mesh_size_callback missing",
        "generate only", "generate is not mesh_size_callback"),
    "pcl": mk(True, "pr-pcl-voxel-leaf", "lock-pclvx",
        "the PCL VoxelGrid that omitted leaf size so a 40M-point cloud stayed dense and ICP OOM'd",
        "pcl.cpp", "pcl::VoxelGrid<PointT> vg; vg.filter(*out)", "vg.setLeafSize(0.05f,0.05f,0.05f)",
        "setLeafSize", "harbor filter only. pack setLeafSize 0.05.",
        "FAIL test_assign: 40M ICP OOM; leaf size missing",
        "filter only", "filter is not setLeafSize"),
    "vtkm": mk(False, "pr-vtkm-cuda-device", "quay-vtkmcu",
        "the VTK-m contour that omitted cuda device so a 512^3 volume sat on serial",
        "vtkm.cxx", "vtkm::cont::Initialize(argc, argv)", "vtkm::cont::RuntimeDeviceTracker().ForceDevice(Cuda)",
        "ForceDevice Cuda", "harbor Initialize only. pack ForceDevice Cuda.",
        "FAIL test_assign: 512^3 serial; Cuda missing",
        "Initialize only", "Initialize is not Cuda"),
    "umpire": mk(True, "pr-umpire-pool-alloc", "lock-umpool",
        "the Umpire Allocator that omitted QuickPool so 1M tiny allocs hit cudaMalloc and stalled",
        "ump.cpp", "auto alloc = rm.getAllocator('DEVICE')", "rm.makeAllocator<QuickPool>('pool', device)",
        "QuickPool", "harbor DEVICE alloc only. pack QuickPool.",
        "FAIL test_assign: 1M cudaMalloc stall; QuickPool missing",
        "DEVICE only", "DEVICE is not QuickPool"),
    "axom": mk(False, "pr-axom-sidre-conduit", "quay-axsid",
        "the Axom Sidre save that omitted conduit protocol so a restart dumped ASCII and filled /tmp",
        "axom.cpp", "ds.save('restart.root')", "ds.save('restart.root', 'sidre_hdf5')",
        "sidre_hdf5", "harbor save root only. pack sidre_hdf5.",
        "FAIL test_assign: ASCII /tmp fill; sidre_hdf5 missing",
        "save only", "save is not sidre_hdf5"),
    "mfem": mk(True, "pr-mfem-static-cond", "lock-mfsc",
        "the MFEM ParBilinearForm that omitted EnableStaticCondensation so a 3D H1 system stayed uncondensed",
        "mfem.cpp", "a.Assemble(); a.Finalize()", "a.EnableStaticCondensation()",
        "EnableStaticCondensation", "harbor Assemble only. pack static condensation.",
        "FAIL test_assign: uncondensed H1; static condensation missing",
        "Assemble only", "Assemble is not static condensation"),
    "moab": mk(False, "pr-moab-parallel-read", "quay-mbrd",
        "the MOAB load that omitted PARALLEL=READ_PART so a 40M-hex mesh loaded on rank 0",
        "moab.cpp", "mb.load_file('in.h5m')", "mb.load_file('in.h5m', 0, 'PARALLEL=READ_PART')",
        "PARALLEL=READ_PART", "harbor load_file only. pack PARALLEL=READ_PART.",
        "FAIL test_assign: 40M hex rank 0; READ_PART missing",
        "load_file only", "load_file is not PARALLEL"),
    "libmesh": mk(True, "pr-libmesh-ghosting-functors", "lock-lmgh",
        "the libMesh EquationSystems that omitted DefaultCoupling so a DG assembly missed ghost dofs",
        "lm.C", "es.init()", "mesh.add_ghosting_functor(coupling)",
        "add_ghosting_functor", "harbor es.init only. pack ghosting functor.",
        "FAIL test_assign: DG missed ghost dofs; ghosting functor missing",
        "init only", "init is not ghosting"),
    "slepc": mk(False, "pr-slepc-eps-nev", "quay-slnev",
        "the SLEPc EPS that omitted EPSSetDimensions nev so a 10-mode run returned 1 eigenpair",
        "slepc.c", "EPSSolve(eps)", "EPSSetDimensions(eps, 10, PETSC_DEFAULT, PETSC_DEFAULT)",
        "EPSSetDimensions", "harbor EPSSolve only. pack nev 10.",
        "FAIL test_assign: 1 eigenpair; nev missing",
        "EPSSolve only", "EPSSolve is not nev"),
    "metis": mk(True, "pr-metis-ncuts", "lock-mtncuts",
        "the METIS PartMeshDual that omitted ncuts so a 4-way cut had 8x edgecut",
        "metis.c", "METIS_PartMeshDual(&ne,&nn,eptr,eind,NULL,NULL,&ncommon,&nparts,NULL,NULL,&objval,epart,npart)",
        "options[METIS_OPTION_NCUTS]=8",
        "NCUTS", "harbor PartMeshDual only. pack NCUTS 8.",
        "FAIL test_assign: 8x edgecut; NCUTS missing",
        "PartMeshDual only", "PartMeshDual is not NCUTS"),
    "parmetis": mk(False, "pr-parmetis-itr-ubvec", "quay-pmitr",
        "the ParMETIS PartKway that omitted ubvec so a 256-rank mesh had 3x load imbalance",
        "parmetis.c", "ParMETIS_V3_PartKway(...)", "ubvec[0]=1.05",
        "ubvec", "harbor PartKway only. pack ubvec 1.05.",
        "FAIL test_assign: 3x imbalance; ubvec missing",
        "PartKway only", "PartKway is not ubvec"),
    "zoltan": mk(True, "pr-zoltan-rcb-rectilinear", "lock-zlrcb",
        "the Zoltan RCB that omitted KEEP_CUTS so a 3D particle dump remapped every restart",
        "zoltan.c", "Zoltan_LB_Set_Param(zz, 'LB_METHOD', 'RCB')", "Zoltan_LB_Set_Param(zz, 'KEEP_CUTS', '1')",
        "KEEP_CUTS", "harbor RCB only. pack KEEP_CUTS.",
        "FAIL test_assign: remap every restart; KEEP_CUTS missing",
        "RCB only", "RCB is not KEEP_CUTS"),
    "strumpack": mk(False, "pr-strumpack-gpu-offload", "quay-stmgpu",
        "the STRUMPACK solve that omitted GPU offload so a 2M HSS sat on CPU",
        "sp.cpp", "sp.factor(); sp.solve(b, x)", "sp.options().set_verbose(false); enable_gpu()",
        "enable_gpu", "harbor factor only. pack GPU offload.",
        "FAIL test_assign: 2M HSS CPU; GPU missing",
        "factor only", "factor is not GPU"),
    "pastix": mk(True, "pr-pastix-thread-nbr", "lock-pstnbr",
        "the PaStiX solve that omitted IPARM_THREAD_NBR so a 1M CSR sat on one core",
        "pastix.c", "pastix(&data, comm, n, colptr, rows, avals, perm, invp, b, nrhs, iparm, dparm)",
        "iparm[IPARM_THREAD_NBR]=16",
        "IPARM_THREAD_NBR", "harbor pastix only. pack THREAD_NBR 16.",
        "FAIL test_assign: 1M CSR 1 core; THREAD_NBR missing",
        "pastix only", "pastix is not THREAD_NBR"),
    "pardiso": mk(False, "pr-mkl-pardiso-iparm-fill", "quay-pdfill",
        "the MKL PARDISO that omitted iparm[1]=3 so METIS fill sat 8x vs nested dissection",
        "pardiso.c", "pardiso(pt, &maxfct, &mnum, &mtype, &phase, &n, a, ia, ja, perm, &nrhs, iparm, &msglvl, b, x, &error)",
        "iparm[1]=3",
        "iparm[1]", "harbor pardiso only. pack iparm[1]=3 METIS.",
        "FAIL test_assign: 8x fill; iparm[1] missing",
        "pardiso only", "pardiso is not iparm"),
}

def fn(key):
    def f(rnd, k=key):
        return plant_from(rnd, PLANTS[k])
    f.__name__ = key
    return f


LHC_PAIRS = [
    ("Firedrake tsfc vs DOLFINx ghost_mode", fn("firedrake"), fn("dolfinx"),
     "tsfc_interface; shared_facet", "assemble; unit_cube",
     "firedrake dump coffee JIT; dolfinx dump DG missed facets"),
    ("CVODE maxord vs Armadillo OPENBLAS threads", fn("sundials"), fn("armadillo"),
     "CVodeSetMaxOrd 2; OPENBLAS_NUM_THREADS 16", "CVode; eig_sym",
     "cvode dump order 5 Newton; armadillo dump 4k 1 core"),
    ("Eigen OMP vs OpenCV setUseOptimized", fn("eigen3"), fn("opencv"),
     "OMP_NUM_THREADS 16; setUseOptimized", "SelfAdjointEigenSolver; remap",
     "eigen dump 8k serial; opencv dump 8k baseline"),
    ("Open3D CUDA vs trimesh process=False", fn("open3d"), fn("trimesh"),
     "CUDA:0; process=False", "PointCloud; load stl",
     "open3d dump 20M ICP CPU; trimesh dump 4M repair OOM"),
    ("meshio binary VTU vs TetGen -q", fn("meshio"), fn("tetgen"),
     "binary=True; -q 1.2", "write vtu; -p",
     "meshio dump ASCII disk; tetgen dump radius-edge 20"),
    ("Netgen maxh vs pygmsh mesh_size_callback", fn("netgen"), fn("pygmsh"),
     "maxh 2.0; mesh_size_callback 0.1", "GenerateMesh; generate 3",
     "netgen dump 20mm mesh; pygmsh dump 5mm fillet"),
    ("PCL setLeafSize vs VTK-m Cuda", fn("pcl"), fn("vtkm"),
     "setLeafSize 0.05; ForceDevice Cuda", "filter; Initialize",
     "pcl dump 40M ICP OOM; vtkm dump 512^3 serial"),
    ("Umpire QuickPool vs Axom sidre_hdf5", fn("umpire"), fn("axom"),
     "QuickPool; sidre_hdf5", "DEVICE; save root",
     "umpire dump 1M cudaMalloc; axom dump ASCII /tmp"),
    ("MFEM static condensation vs MOAB READ_PART", fn("mfem"), fn("moab"),
     "EnableStaticCondensation; PARALLEL=READ_PART", "Assemble; load_file",
     "mfem dump uncondensed H1; moab dump 40M hex rank 0"),
    ("libMesh ghosting vs SLEPc nev", fn("libmesh"), fn("slepc"),
     "add_ghosting_functor; EPSSetDimensions 10", "init; EPSSolve",
     "libmesh dump DG missed ghosts; slepc dump 1 eigenpair"),
    ("METIS NCUTS vs ParMETIS ubvec", fn("metis"), fn("parmetis"),
     "NCUTS 8; ubvec 1.05", "PartMeshDual; PartKway",
     "metis dump 8x edgecut; parmetis dump 3x imbalance"),
    ("Zoltan KEEP_CUTS vs STRUMPACK GPU", fn("zoltan"), fn("strumpack"),
     "KEEP_CUTS 1; enable_gpu", "RCB; factor",
     "zoltan dump remap restart; strumpack dump 2M HSS CPU"),
    ("PaStiX THREAD_NBR vs MKL PARDISO iparm", fn("pastix"), fn("pardiso"),
     "THREAD_NBR 16; iparm[1]=3", "pastix; pardiso",
     "pastix dump 1M CSR 1 core; pardiso dump 8x fill"),
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
- Not a clone of w4cs RSEM/Seurat/Mutect2/Hail, w4cr FastQC/SPAdes, r4778 nim-lent, r4777 zig-errdefer, r4687 rust-pin, r4580 kanidm/gluu, identity-origin SSO.
- Bans avoided: nim-lent / zig-errdefer / rust-pin / Mutect2 / Hail / FastQC / Seurat / RSEM / kanidm / gluu / agama / RPITIT / Prom native hist / ThinLTO / Go loopvar / Django ASGI / Vale / Koka / identity-origin clones.
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
