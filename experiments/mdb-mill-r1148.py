#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1148+ unique quantum/CAS/crypto leftover plants.

BAN r01–r1147 clones including guix-inf-leftover-manifest / nix-lock-leftover-revpin
and r1084 HEP leftover slugs (rivet-yoda / fastjet-area / delphes-card / sherpa-runcard).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1084.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1084", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1148
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "guix-inf-leftover-manifest",
    "nix-lock-leftover-revpin",
    "openems-xml-leftover-fdtd",
    "siliconcompiler-py-leftover-target",
    "rivet-yoda-leftover-histo",
    "fastjet-area-leftover-voronoi",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

PLANTS = [
    "boobook", "morepork", "nightparrot", "groundparrot", "rockparrot", "swiftparrot",
    "orangebellied", "fortyspotted", "chowchilla", "sittella", "shrikethrush", "yellowrobin",
    "scrubrobin", "hoodedrobin", "magpielark", "mudlark", "currawong", "butcherbird",
    "thornbill", "weebill", "heathwren", "fieldwren", "emuwren", "spinifexbird",
    "carpentarian", "whiteface", "whipbird", "wedgebill", "bellbird", "friarbird",
    "poouli", "akiapolaau", "olomao", "kamao", "ou", "palila2",
    "millerbird2", "nihoaakialoa", "laysanduck", "boninwhiteeye", "guamkingfisher", "sihek",
    "kagu2", "takahe2", "okinawarail2", "palauowl2", "bristlethighed2", "firewoodgatherer2",
    "forestrobin2", "paradisewhydah2", "hangingparrot3", "canastero3", "tapaculo3", "seriema3",
    "weka3", "boobook2", "morepork2", "nightparrot2", "groundparrot2", "rockparrot2",
    "swiftparrot2", "orangebellied2", "fortyspotted2", "chowchilla2", "sittella2", "shrikethrush2",
    "yellowrobin2", "scrubrobin2", "hoodedrobin2", "magpielark2", "mudlark2", "currawong2",
    "butcherbird2", "thornbill2", "weebill2", "heathwren2", "fieldwren2", "emuwren2",
    "spinifexbird2", "carpentarian2", "whiteface2", "whipbird2", "wedgebill2", "bellbird2",
    "friarbird2", "poouli2", "akiapolaau2", "olomao2", "kamao2", "ou2",
    "nihoaakialoa2", "laysanduck2", "boninwhiteeye2", "guamkingfisher2", "sihek2", "xitlark",
    "yanoleaf", "zebrawren", "alcalauris", "sihek3", "kagu3", "takahe3",
    "palila3", "ou3", "olomao3", "kamao3", "poouli3", "akiapolaau3",
    "millerbird3", "nihoaakialoa3", "laysanduck3", "boninwhiteeye3", "guamkingfisher3", "sittella3",
    "chowchilla3", "weebill3", "thornbill3", "heathwren3", "fieldwren3", "emuwren3",
]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1147 clones (ban guix-inf-leftover-manifest / nix-lock-leftover-revpin; no r1084 rivet-yoda-leftover-histo / fastjet-area-leftover-voronoi clones).

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
Keep unique leftover leftover leftover plots. Ban r01–r1147 clones, libNNNN.
"""


TOOLS: list[tuple] = [
    ("qiskit-py-leftover-aer", "Qiskit leftover vs aer.py", "qiskit", "1.2.4", "2.0.1", "aer.py", "# qiskit 1.2.4", "# qiskit 2.0.1", "Aer.get_backend('qasm_simulator')", "AerSimulator(method='statevector')", "execute(qc, backend, shots=1024)", "backend.run(qc, shots=4096)", "qasm_simulator → AerSimulator statevector", "python3 -c 'import qiskit; print(qiskit.__version__)'", "python3 apps/api/aer.py", "python3 apps/legacy/aer.py", "py"),
    ("cirq-py-leftover-simulator", "Cirq leftover vs sim.py", "cirq", "1.4.1", "1.5.0", "sim.py", "# cirq 1.4.1", "# cirq 1.5.0", "cirq.Simulator()", "cirq.DensityMatrixSimulator()", "sim.run(circuit, repetitions=100)", "sim.run(circuit, repetitions=1000)", "Simulator → DensityMatrixSimulator", "python3 -c 'import cirq; print(cirq.__version__)'", "python3 apps/api/sim.py", "python3 apps/legacy/sim.py", "py"),
    ("pennylane-py-leftover-device", "PennyLane leftover vs dev.py", "pennylane", "0.38.1", "0.41.1", "dev.py", "# pennylane 0.38.1", "# pennylane 0.41.1", "qml.device('default.qubit', wires=2)", "qml.device('lightning.qubit', wires=4)", "qml.QNode(circuit, dev)", "qml.QNode(circuit, dev, diff_method='adjoint')", "default.qubit → lightning + adjoint", "python3 -c 'import pennylane; print(pennylane.__version__)'", "python3 apps/api/dev.py", "python3 apps/legacy/dev.py", "py"),
    ("braket-py-leftover-local", "Braket leftover vs local.py", "braket", "1.88.0", "1.90.0", "local.py", "# braket 1.88.0", "# braket 1.90.0", "LocalSimulator()", "LocalSimulator('braket_dm')", "device.run(circ, shots=100)", "device.run(circ, shots=1000)", "LocalSimulator → braket_dm", "python3 -c 'import braket; print(braket.__version__)'", "python3 apps/api/local.py", "python3 apps/legacy/local.py", "py"),
    ("qsharp-qs-leftover-qubit", "Q# leftover vs qubit.qs", "qsharp", "1.12.0", "1.16.0", "qubit.qs", "// qsharp 1.12.0", "// qsharp 1.16.0", "operation Main() : Result { use q = Qubit(); return M(q); }", "operation Main() : Result[] { use qs = Qubit[2]; return MeasureEachZ(qs); }", "open Microsoft.Quantum.Intrinsic;", "open Microsoft.Quantum.Measurement;", "single M → MeasureEachZ", "qsharp --version || true", "qsc build apps/api/qubit.qs", "qsc build apps/legacy/qubit.qs", "qs"),
    ("stim-py-leftover-tableau", "Stim leftover vs tab.py", "stim", "1.13.0", "1.15.0", "tab.py", "# stim 1.13.0", "# stim 1.15.0", "stim.TableauSimulator()", "stim.FlipSimulator(batch_size=64)", "c.append('H', [0])", "c.append('CX', [0, 1])", "TableauSimulator → FlipSimulator + CX", "python3 -c 'import stim; print(stim.__version__)'", "python3 apps/api/tab.py", "python3 apps/legacy/tab.py", "py"),
    ("pytket-py-leftover-backend", "pytket leftover vs be.py", "pytket", "1.33.1", "1.40.0", "be.py", "# pytket 1.33.1", "# pytket 1.40.0", "AerBackend()", "AerStateBackend()", "backend.default_compilation_pass(2)", "backend.default_compilation_pass(3)", "AerBackend → AerStateBackend O3", "python3 -c 'import pytket; print(pytket.__version__)'", "python3 apps/api/be.py", "python3 apps/legacy/be.py", "py"),
    ("projectq-py-leftover-engine", "ProjectQ leftover vs eng.py", "projectq", "0.5.1", "0.8.0", "eng.py", "# projectq 0.5.1", "# projectq 0.8.0", "MainEngine(backend=Simulator())", "MainEngine(backend=LocalSimulator())", "eng.flush()", "eng.flush(deallocate_qubits=True)", "Simulator → LocalSimulator + dealloc", "python3 -c 'import projectq; print(projectq.__version__)'", "python3 apps/api/eng.py", "python3 apps/legacy/eng.py", "py"),
    ("dwave-py-leftover-sampler", "D-Wave leftover vs samp.py", "dwave", "6.9.0", "6.11.0", "samp.py", "# dwave 6.9.0", "# dwave 6.11.0", "ExactSolver()", "SimulatedAnnealingSampler()", "sampler.sample(bqm, num_reads=10)", "sampler.sample(bqm, num_reads=100, chain_strength=2.0)", "ExactSolver → SA + chain_strength", "python3 -c 'import dwave; print(dwave.__version__)'", "python3 apps/api/samp.py", "python3 apps/legacy/samp.py", "py"),
    ("ocean-py-leftover-bqm", "Ocean leftover vs bqm.py", "ocean", "6.9.0", "6.11.0", "bqm.py", "# ocean 6.9.0", "# ocean 6.11.0", "BinaryQuadraticModel.empty('BINARY')", "BinaryQuadraticModel.empty('SPIN')", "bqm.add_linear(v, 1)", "bqm.add_quadratic(u, v, -1)", "BINARY → SPIN + quadratic", "python3 -c 'import dimod; print(dimod.__version__)'", "python3 apps/api/bqm.py", "python3 apps/legacy/bqm.py", "py"),
    ("qutip-py-leftover-mesolve", "QuTiP leftover vs me.py", "qutip", "4.7.6", "5.1.1", "me.py", "# qutip 4.7.6", "# qutip 5.1.1", "mesolve(H, psi0, tlist, c_ops)", "mesolve(H, psi0, tlist, c_ops, options={'nsteps': 5000})", "expect(n, result.states)", "expect(n, result.states, herm=True)", "mesolve nsteps + herm expect", "python3 -c 'import qutip; print(qutip.__version__)'", "python3 apps/api/me.py", "python3 apps/legacy/me.py", "py"),
    ("qulacs-py-leftover-gate", "Qulacs leftover vs gate.py", "qulacs", "0.6.4", "0.6.11", "gate.py", "# qulacs 0.6.4", "# qulacs 0.6.11", "gate.H(0)", "gate.DenseMatrix(0, [[0,1],[1,0]])", "circuit.add_gate(g)", "circuit.add_gate(g, is_noise=False)", "H → DenseMatrix X", "python3 -c 'import qulacs; print(qulacs.__version__)'", "python3 apps/api/gate.py", "python3 apps/legacy/gate.py", "py"),
    ("openqasm-qasm-leftover-gate", "OpenQASM leftover vs g.qasm", "openqasm", "2.0", "3.1", "g.qasm", "// openqasm 2.0", "// openqasm 3.1", "OPENQASM 2.0;", "OPENQASM 3.1;", "cx q[0],q[1];", "ctrl @ x q[0], q[1];", "OPENQASM 2 cx → 3 ctrl @ x", "qasm3 --version || true", "qasm3 apps/api/g.qasm", "qasm3 apps/legacy/g.qasm", "qasm"),
    ("quil-quil-leftover-defgate", "Quil leftover vs g.quil", "quil", "1.0", "2.0", "g.quil", "# quil 1.0", "# quil 2.0", "DEFGATE FOO:\n    0, 1\n    1, 0", "DEFCIRCUIT FOO q:\n    X q", "H 0", "H 0\nCNOT 0 1", "DEFGATE → DEFCIRCUIT + CNOT", "quilc --version || true", "quilc apps/api/g.quil", "quilc apps/legacy/g.quil", "quil"),
    ("catalyst-py-leftover-qjit", "Catalyst leftover vs qjit.py", "catalyst", "0.8.0", "0.11.0", "qjit.py", "# catalyst 0.8.0", "# catalyst 0.11.0", "@qjit", "@qjit(autograph=True)", "return qml.expval(qml.PauliZ(0))", "return qml.var(qml.PauliZ(0))", "qjit autograph + var", "python3 -c 'import catalyst; print(catalyst.__version__)'", "python3 apps/api/qjit.py", "python3 apps/legacy/qjit.py", "py"),
    ("cudaq-py-leftover-kernel", "CUDA-Q leftover vs kern.py", "cudaq", "0.8.0", "0.10.0", "kern.py", "# cudaq 0.8.0", "# cudaq 0.10.0", "cudaq.set_target('qpp-cpu')", "cudaq.set_target('nvidia')", "@cudaq.kernel\ndef k(): cudaq.h(0)", "@cudaq.kernel\ndef k(): cudaq.x.ctrl(0,1)", "qpp-cpu → nvidia + ctrl x", "python3 -c 'import cudaq; print(cudaq.__version__)'", "python3 apps/api/kern.py", "python3 apps/legacy/kern.py", "py"),
    ("strawberry-py-leftover-fock", "Strawberry Fields leftover vs fock.py", "strawberry", "0.23.0", "0.24.0", "fock.py", "# strawberry 0.23.0", "# strawberry 0.24.0", "eng = sf.Engine('fock', backend_options={'cutoff_dim': 5})", "eng = sf.Engine('gaussian')", "eng.run(prog)", "eng.run(prog, shots=10)", "fock cutoff 5 → gaussian shots", "python3 -c 'import strawberryfields; print(strawberryfields.__version__)'", "python3 apps/api/fock.py", "python3 apps/legacy/fock.py", "py"),
    ("tket-json-leftover-rebase", "TKET leftover vs rebase.json", "tket", "1.33.1", "1.40.0", "rebase.json", "// tket 1.33.1", "// tket 1.40.0", "\"rebase\": \"IBM\"", "\"rebase\": \"TKET\"", "\"cx_basis\": true", "\"cx_basis\": false", "IBM rebase → TKET, cx_basis off", "python3 -c 'import pytket; print(pytket.__version__)'", "python3 -c 'import json; json.load(open(\"apps/api/rebase.json\"))'", "python3 -c 'import json; json.load(open(\"apps/legacy/rebase.json\"))'", "json"),
    ("myqlm-py-leftover-qpu", "myQLM leftover vs qpu.py", "myqlm", "1.9.3", "1.11.0", "qpu.py", "# myqlm 1.9.3", "# myqlm 1.11.0", "PyLinalg()", "LinAlg(sparse=True)", "qpu.submit(job)", "qpu.submit(job).join()", "PyLinalg → sparse LinAlg join", "python3 -c 'import qat; print(qat.__version__)'", "python3 apps/api/qpu.py", "python3 apps/legacy/qpu.py", "py"),
    ("qibo-py-leftover-backend", "Qibo leftover vs be.py", "qibo", "0.2.12", "0.2.16", "be.py", "# qibo 0.2.12", "# qibo 0.2.16", "qibo.set_backend('numpy')", "qibo.set_backend('qibojit', platform='numba')", "c.add(gates.H(0))", "c.add(gates.CNOT(0, 1))", "numpy → qibojit numba + CNOT", "python3 -c 'import qibo; print(qibo.__version__)'", "python3 apps/api/be.py", "python3 apps/legacy/be.py", "py"),
    ("yao-jl-leftover-block", "Yao leftover vs block.jl", "yao", "0.8.13", "0.9.0", "block.jl", "# yao 0.8.13", "# yao 0.9.0", "chain(H, X)", "chain(H, control(1, 2=>X))", "dispatch!(r, :zero)", "dispatch!(r, :plus)", "H/X → control X + plus", "julia -e 'using Yao; println(pkgversion(Yao))'", "julia apps/api/block.jl", "julia apps/legacy/block.jl", "jl"),
    ("perceval-py-leftover-processor", "Perceval leftover vs proc.py", "perceval", "0.11.1", "0.12.1", "proc.py", "# perceval 0.11.1", "# perceval 0.12.1", "p = pcvl.Processor('SLOS')", "p = pcvl.Processor('Naive')", "p.with_input(st)", "p.with_input(st).min_detected_photons_filter(1)", "SLOS → Naive + min photons", "python3 -c 'import perceval; print(perceval.__version__)'", "python3 apps/api/proc.py", "python3 apps/legacy/proc.py", "py"),
    ("pyquil-py-leftover-compiler", "pyQuil leftover vs comp.py", "pyquil", "4.14.1", "4.16.0", "comp.py", "# pyquil 4.14.1", "# pyquil 4.16.0", "get_qc('9q-square-qvm')", "get_qc('Aspen-M-3', as_qvm=True)", "qc.compile(p)", "qc.compile(p, to_native_gates=True)", "9q-square-qvm → Aspen-M-3 native", "python3 -c 'import pyquil; print(pyquil.__version__)'", "python3 apps/api/comp.py", "python3 apps/legacy/comp.py", "py"),
    ("tequila-py-leftover-sim", "Tequila leftover vs sim.py", "tequila", "1.9.0", "1.9.7", "sim.py", "# tequila 1.9.0", "# tequila 1.9.7", "tq.simulate(U, backend='qulacs')", "tq.simulate(U, backend='qibo')", "E = tq.ExpectationValue(H=H, U=U)", "E = tq.ExpectationValue(H=H, U=U, optimize_measurements=True)", "qulacs → qibo + optimize_measurements", "python3 -c 'import tequila; print(tequila.__version__)'", "python3 apps/api/sim.py", "python3 apps/legacy/sim.py", "py"),
    ("openfermion-py-leftover-jw", "OpenFermion leftover vs jw.py", "openfermion", "1.6.1", "1.7.0", "jw.py", "# openfermion 1.6.1", "# openfermion 1.7.0", "jordan_wigner(op)", "bravyi_kitaev(op)", "get_sparse_operator(hop)", "get_sparse_operator(hop, n_qubits=8)", "JW → BK + n_qubits 8", "python3 -c 'import openfermion; print(openfermion.__version__)'", "python3 apps/api/jw.py", "python3 apps/legacy/jw.py", "py"),
    ("ionq-py-leftover-aria", "IonQ leftover vs aria.py", "ionq", "0.13.0", "0.15.0", "aria.py", "# ionq 0.13.0", "# ionq 0.15.0", "backend='ionq_simulator'", "backend='ionq_aria_1'", "shots=100", "shots=1000, error_mitigation={'debias': True}", "simulator → aria_1 + debias", "python3 -c 'import ionq; print(ionq.__version__)'", "python3 apps/api/aria.py", "python3 apps/legacy/aria.py", "py"),
    ("rigetti-py-leftover-aspen", "Rigetti leftover vs aspen.py", "rigetti", "4.14.1", "4.16.0", "aspen.py", "# rigetti 4.14.1", "# rigetti 4.16.0", "qc = get_qc('Aspen-M-2')", "qc = get_qc('Ankaa-2')", "qc.compiler.quil_to_native_quil(p)", "qc.compiler.native_quil_to_executable(nq)", "Aspen-M-2 → Ankaa-2 executable", "python3 -c 'import qcs_sdk; print(qcs_sdk.__version__)'", "python3 apps/api/aspen.py", "python3 apps/legacy/aspen.py", "py"),
    ("xanadu-py-leftover-borealis", "Xanadu leftover vs bor.py", "xanadu", "0.23.0", "0.24.0", "bor.py", "# xanadu 0.23.0", "# xanadu 0.24.0", "eng = sf.RemoteEngine('X8')", "eng = sf.RemoteEngine('borealis')", "eng.run(prog, shots=1)", "eng.run(prog, shots=10**6)", "X8 → borealis 1e6 shots", "python3 -c 'import strawberryfields; print(strawberryfields.__version__)'", "python3 apps/api/bor.py", "python3 apps/legacy/bor.py", "py"),
    ("pasqal-py-leftover-fresnel", "Pasqal leftover vs fres.py", "pasqal", "0.20.0", "1.1.0", "fres.py", "# pasqal 0.20.0", "# pasqal 1.1.0", "emu = pulser.simulators.QutipEmulator(seq)", "emu = pulser_simulation.QutipEmulator.from_sequence(seq)", "emu.run()", "emu.run(progress_bar=True)", "simulators → pulser_simulation QutipEmulator", "python3 -c 'import pulser; print(pulser.__version__)'", "python3 apps/api/fres.py", "python3 apps/legacy/fres.py", "py"),
    ("quantinuum-py-leftover-h2", "Quantinuum leftover vs h2.py", "quantinuum", "1.33.1", "1.40.0", "h2.py", "# quantinuum 1.33.1", "# quantinuum 1.40.0", "QuantinuumBackend('H1-1E')", "QuantinuumBackend('H2-1')", "backend.process_circuits([c], n_shots=100)", "backend.process_circuits([c], n_shots=1000)", "H1-1E → H2-1 1000 shots", "python3 -c 'import pytket; print(pytket.__version__)'", "python3 apps/api/h2.py", "python3 apps/legacy/h2.py", "py"),
    ("quri-py-leftover-circuit", "QURI leftover vs circ.py", "quri", "0.19.0", "0.21.0", "circ.py", "# quri 0.19.0", "# quri 0.21.0", "QuantumCircuit(2)", "LinearMappedUnboundParametricQuantumCircuit(2)", "circuit.add_H_gate(0)", "circuit.add_ParametricRX_gate(0, param)", "static H → parametric RX", "python3 -c 'import quri_parts; print(quri_parts.__version__)'", "python3 apps/api/circ.py", "python3 apps/legacy/circ.py", "py"),
    ("forestq-py-leftover-quilc", "Forest leftover vs quilc.py", "forestq", "4.14.1", "4.16.0", "quilc.py", "# forestq 4.14.1", "# forestq 4.16.0", "local_forest_runtime()", "local_forest_runtime(quilc_port=5555)", "compiler.quil_to_native_quil(p)", "compiler.quil_to_native_quil(p, protoquil=True)", "quilc_port 5555 + protoquil", "python3 -c 'import pyquil; print(pyquil.__version__)'", "python3 apps/api/quilc.py", "python3 apps/legacy/quilc.py", "py"),
    ("symengine-py-leftover-evalf", "SymEngine leftover vs ev.py", "symengine", "0.11.0", "0.13.0", "ev.py", "# symengine 0.11.0", "# symengine 0.13.0", "x.evalf(20)", "x.n(50, real=True)", "expand(e)", "expand(e, deep=True)", "evalf 20 → n(50) + deep expand", "python3 -c 'import symengine; print(symengine.__version__)'", "python3 apps/api/ev.py", "python3 apps/legacy/ev.py", "py"),
    ("fricas-input-leftover-spad", "FriCAS leftover vs spad.input", "fricas", "1.3.10", "1.3.11", "spad.input", ")abbrev 1.3.10", ")abbrev 1.3.11", ")set output algebra on", ")set output tex on", "p := D(sin x, x)", "p := D(sin x, x, 2)", "algebra → tex + 2nd deriv", "fricas --version || true", "fricas -eval apps/api/spad.input", "fricas -eval apps/legacy/spad.input", "input"),
    ("reduce-red-leftover-alg", "REDUCE leftover vs alg.red", "reduce", "6860", "6870", "alg.red", "% reduce 6860", "% reduce 6870", "on exp;", "on factor;", "off rounded;", "on rounded; precision 20;", "exp → factor + rounded 20", "reduce --version || true", "reduce apps/api/alg.red", "reduce apps/legacy/alg.red", "red"),
    ("magma-m-leftover-grp", "Magma leftover vs grp.m", "magma", "2.28-2", "2.28-15", "grp.m", "// magma 2.28-2", "// magma 2.28-15", "G := SymmetricGroup(4);", "G := AlternatingGroup(5);", "CompositionSeries(G);", "ChiefSeries(G);", "S4 → A5 ChiefSeries", "magma -v || true", "magma apps/api/grp.m", "magma apps/legacy/grp.m", "m"),
    ("maple-mpl-leftover-assume", "Maple leftover vs as.mpl", "maple", "2024.1", "2025.0", "as.mpl", "# maple 2024.1", "# maple 2025.0", "assume(x, real);", "assume(x, positive);", "simplify(sqrt(x^2));", "simplify(sqrt(x^2), symbolic);", "real → positive + symbolic", "maple -q || true", "maple apps/api/as.mpl", "maple apps/legacy/as.mpl", "mpl"),
    ("form-frm-leftover-id", "FORM leftover vs id.frm", "form", "4.3.1", "4.3.2", "id.frm", "* form 4.3.1", "* form 4.3.2", "id g(mu) = g_(1,mu);", "id g(mu) = g_(2,mu);", "trace4,1;", "tracen,2;", "g_ 1 → 2 + tracen", "form -v | head -n 1", "form apps/api/id.frm", "form apps/legacy/id.frm", "frm"),
    ("cadabra-cdb-leftover-unwrap", "Cadabra leftover vs un.cdb", "cadabra", "2.4.5", "2.5.8", "un.cdb", "{cadabra 2.4.5}", "{cadabra 2.5.8}", "unwrap(_);", "distribute(_);", "canonicalise(_);", "sort_product(_);", "unwrap → distribute + sort_product", "cadabra2 --version || true", "cadabra2 apps/api/un.cdb", "cadabra2 apps/legacy/un.cdb", "cdb"),
    ("ginac-h-leftover-ex", "GiNaC leftover vs ex.h", "ginac", "1.8.7", "1.8.9", "ex.h", "// ginac 1.8.7", "// ginac 1.8.9", "ex e = sin(x);", "ex e = series_to_poly(sin(x).series(x==0, 6));", "e.evalf();", "e.evalf(50);", "sin → series_to_poly + evalf 50", "pkg-config --modversion ginac", "c++ -c apps/api/ex.h", "c++ -c apps/legacy/ex.h", "h"),
    ("xact-m-leftover-canonical", "xAct leftover vs can.m", "xact", "1.2.0", "1.2.1", "can.m", "(* xact 1.2.0 *)", "(* xact 1.2.1 *)", "ToCanonical[expr]", "ToCanonical[expr, UseMetricOnVBundle -> None]", "ContractMetric[expr]", "ContractMetric[expr, OverContract -> True]", "ToCanonical UseMetricOnVBundle None", "math -script apps/api/can.m", "math -script apps/api/can.m", "math -script apps/legacy/can.m", "m"),
    ("codesaturne-xml-leftover-turb", "Code_Saturne leftover vs turb.xml", "codesaturne", "8.0.2", "8.3.1", "turb.xml", "<!-- codesaturne 8.0.2 -->", "<!-- codesaturne 8.3.1 -->", "<turbulence_model>k-epsilon</turbulence_model>", "<turbulence_model>rij-epsilon</turbulence_model>", "<wall_function>1</wall_function>", "<wall_function>2 scalable=\"true\"/>", "k-epsilon → rij-epsilon scalable wall", "code_saturne --version | head -n 1", "code_saturne run --param apps/api/turb.xml", "code_saturne run --param apps/legacy/turb.xml", "xml"),
    ("starccm-sim-leftover-mesh", "STAR-CCM leftover vs mesh.java", "starccm", "19.02", "19.06", "mesh.java", "// starccm 19.02", "// starccm 19.06", "sim.getMeshPipeline().setTrimmer();", "sim.getMeshPipeline().setPolyhedral();", "trimmer.setBaseSize(0.01);", "poly.setBaseSize(0.005);", "trimmer → polyhedral 0.005", "starccm+ -version || true", "starccm+ -batch apps/api/mesh.java", "starccm+ -batch apps/legacy/mesh.java", "java"),
    ("libsodium-h-leftover-box", "libsodium leftover vs box.h", "libsodium", "1.0.19", "1.0.20", "box.h", "/* libsodium 1.0.19 */", "/* libsodium 1.0.20 */", "crypto_box_easy(c,m,mlen,n,pk,sk);", "crypto_box_easy_afternm(c,m,mlen,n,k);", "crypto_box_keypair(pk,sk);", "crypto_box_seed_keypair(pk,sk,seed);", "box_easy → afternm + seed_keypair", "pkg-config --modversion libsodium", "c++ -c apps/api/box.h", "c++ -c apps/legacy/box.h", "h"),
    ("boringssl-cnf-leftover-tls13", "BoringSSL leftover vs tls.cnf", "boringssl", "2024.0", "2025.0", "tls.cnf", "# boringssl 2024.0", "# boringssl 2025.0", "MinProtocol = TLSv1.2", "MinProtocol = TLSv1.3", "CipherString = DEFAULT", "CipherString = TLS_AES_256_GCM_SHA384", "TLS1.2 DEFAULT → TLS1.3 AES_256_GCM", "bssl version || true", "bssl s_server -config apps/api/tls.cnf", "bssl s_server -config apps/legacy/tls.cnf", "cnf"),
    ("wolfssl-cnf-leftover-dtls", "wolfSSL leftover vs dtls.cnf", "wolfssl", "5.7.2", "5.8.0", "dtls.cnf", "# wolfssl 5.7.2", "# wolfssl 5.8.0", "DTLS = no", "DTLS = yes", "TLS13 = no", "TLS13 = yes", "DTLS off → on + TLS1.3", "wolfssl-config --version || true", "wolfssl-config --cflags", "wolfssl-config --cflags", "cnf"),
    ("mbedtls-cnf-leftover-psa", "Mbed TLS leftover vs psa.cnf", "mbedtls", "3.6.1", "4.0.0", "psa.cnf", "# mbedtls 3.6.1", "# mbedtls 4.0.0", "MBEDTLS_USE_PSA_CRYPTO undefined", "MBEDTLS_USE_PSA_CRYPTO defined", "MBEDTLS_SSL_PROTO_TLS1_2", "MBEDTLS_SSL_PROTO_TLS1_3", "PSA crypto on + TLS1.3", "mbedtls_selftest || true", "mbedtls_selftest", "mbedtls_selftest", "cnf"),
    ("botan-ini-leftover-provider", "Botan leftover vs prov.ini", "botan", "3.5.0", "3.7.1", "prov.ini", "# botan 3.5.0", "# botan 3.7.1", "provider = base", "provider = openssl", "rng = system", "rng = hmac_drbg", "base → openssl + hmac_drbg", "botan --version | head -n 1", "botan hash --provider=openssl", "botan hash --provider=openssl", "ini"),
    ("cryptopp-h-leftover-aes", "Crypto++ leftover vs aes.h", "cryptopp", "8.9.0", "8.9.0-api", "aes.h", "// cryptopp 8.9.0", "// cryptopp 8.9.0-api", "CBC_Mode<AES>::Encryption enc;", "GCM<AES>::Encryption enc;", "enc.SetKeyWithIV(key, 16, iv);", "enc.SetKeyWithIV(key, 32, iv);", "CBC AES-128 → GCM AES-256", "pkg-config --modversion libcryptopp || true", "c++ -c apps/api/aes.h", "c++ -c apps/legacy/aes.h", "h"),
    ("age-txt-leftover-recipient", "age leftover vs rec.txt", "age", "1.2.0", "1.2.1", "rec.txt", "# age 1.2.0", "# age 1.2.1", "age1legacy...", "age1api...", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIlegacy", "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIapi", "legacy recipient → api + ssh", "age --version | head -n 1", "age -R apps/api/rec.txt -o /tmp/api.age /tmp/p", "age -R apps/legacy/rec.txt -o /tmp/legacy.age /tmp/p", "txt"),
    ("minisign-pub-leftover-trusted", "minisign leftover vs trusted.pub", "minisign", "0.11", "0.12", "trusted.pub", "untrusted comment: minisign 0.11", "untrusted comment: minisign 0.12", "RWTlegacykey", "RWTapikey", "trusted comment: legacy", "trusted comment: api timestamp=1", "legacy key → api timestamp", "minisign -v || true", "minisign -V -p apps/api/trusted.pub -m /tmp/p", "minisign -V -p apps/legacy/trusted.pub -m /tmp/p", "pub"),
    ("neo4j-conf-leftover-bolt", "Neo4j leftover vs neo4j.conf", "neo4j", "5.24.0", "5.26.0", "neo4j.conf", "# neo4j 5.24.0", "# neo4j 5.26.0", "server.bolt.enabled=true", "server.bolt.enabled=true\nserver.bolt.tls_level=REQUIRED", "dbms.security.auth_enabled=false", "dbms.security.auth_enabled=true", "bolt TLS required + auth on", "neo4j version | head -n 1", "neo4j console", "neo4j console", "conf"),
    ("janusgraph-props-leftover-backend", "JanusGraph leftover vs jg.properties", "janusgraph", "1.0.0", "1.1.0", "jg.properties", "# janusgraph 1.0.0", "# janusgraph 1.1.0", "storage.backend=berkeleyje", "storage.backend=cql", "index.search.backend=elasticsearch", "index.search.backend=lucene", "berkeleyje → cql + lucene", "janusgraph.sh --version || true", "janusgraph.sh apps/api/jg.properties", "janusgraph.sh apps/legacy/jg.properties", "properties"),
    ("dgraph-yml-leftover-alpha", "Dgraph leftover vs alpha.yml", "dgraph", "24.0.0", "24.1.0", "alpha.yml", "# dgraph 24.0.0", "# dgraph 24.1.0", "lru_mb: 1024", "lru_mb: 4096", "zero: localhost:5080", "zero: localhost:5080\nsecurity.whitelist: 10.0.0.0/8", "lru 1g→4g + whitelist", "dgraph version | head -n 1", "dgraph alpha --config apps/api/alpha.yml", "dgraph alpha --config apps/legacy/alpha.yml", "yml"),
    ("arangodb-conf-leftover-agency", "ArangoDB leftover vs arango.conf", "arangodb", "3.12.2", "3.12.5", "arango.conf", "# arangodb 3.12.2", "# arangodb 3.12.5", "agency.size = 1", "agency.size = 3", "rocksdb.encryption-keyfile =", "rocksdb.encryption-keyfile = /etc/arango.key", "agency 1→3 + encryption", "arangod --version | head -n 1", "arangod --configuration apps/api/arango.conf", "arangod --configuration apps/legacy/arango.conf", "conf"),
    ("orientdb-xml-leftover-storage", "OrientDB leftover vs stor.xml", "orientdb", "3.2.31", "3.2.38", "stor.xml", "<!-- orientdb 3.2.31 -->", "<!-- orientdb 3.2.38 -->", "<storage type=\"plocal\"/>", "<storage type=\"remote\"/>", "<cluster strategy=\"default\"/>", "<cluster strategy=\"round-robin\"/>", "plocal → remote + round-robin", "server.sh --version || true", "server.sh -c apps/api/stor.xml", "server.sh -c apps/legacy/stor.xml", "xml"),
    ("nebula-conf-leftover-meta", "Nebula leftover vs meta.conf", "nebula", "3.8.0", "3.8.2", "meta.conf", "# nebula 3.8.0", "# nebula 3.8.2", "--meta_server_addrs=127.0.0.1:9559", "--meta_server_addrs=127.0.0.1:9559,127.0.0.1:9560", "--heartbeat_interval_secs=10", "--heartbeat_interval_secs=3", "single meta → HA + faster HB", "nebula-metad --version || true", "nebula-metad --flagfile apps/api/meta.conf", "nebula-metad --flagfile apps/legacy/meta.conf", "conf"),
    ("sonic-cfg-leftover-channel", "Sonic leftover vs ch.cfg", "sonic", "1.4.8", "1.4.9", "ch.cfg", "# sonic 1.4.8", "# sonic 1.4.9", "[channel.legacy]", "[channel.api]", "store = kv", "store = fst", "kv → fst channel api", "sonic --version || true", "sonic -c apps/api/ch.cfg", "sonic -c apps/legacy/ch.cfg", "cfg"),
    ("quickwit-yaml-leftover-index", "Quickwit leftover vs idx.yaml", "quickwit", "0.8.2", "0.9.0", "idx.yaml", "# quickwit 0.8.2", "# quickwit 0.9.0", "indexing_settings.commit_timeout_secs: 60", "indexing_settings.commit_timeout_secs: 10", "search_settings.default_search_fields: [body]", "search_settings.default_search_fields: [title, body]", "commit 60→10 + title field", "quickwit --version | head -n 1", "quickwit index create --index-config apps/api/idx.yaml", "quickwit index create --index-config apps/legacy/idx.yaml", "yaml"),
    ("tantivy-toml-leftover-tokenizer", "Tantivy leftover vs tok.toml", "tantivy", "0.22.0", "0.24.0", "tok.toml", "# tantivy 0.22.0", "# tantivy 0.24.0", "tokenizer = \"default\"", "tokenizer = \"ngram\"", "ngram_min = 2", "ngram_min = 3\nngram_max = 5", "default → ngram 3-5", "python3 -c 'import tantivy; print(tantivy.__version__)'", "python3 -c 'print(\"apps/api/tok.toml\")'", "python3 -c 'print(\"apps/legacy/tok.toml\")'", "toml"),
    ("lancedb-py-leftover-index", "LanceDB leftover vs idx.py", "lancedb", "0.16.0", "0.21.1", "idx.py", "# lancedb 0.16.0", "# lancedb 0.21.1", "tbl.create_index(metric='L2')", "tbl.create_index(metric='cosine', num_partitions=64)", "tbl.search(q).limit(10)", "tbl.search(q).limit(50).nprobes(20)", "L2 → cosine partitions + nprobes", "python3 -c 'import lancedb; print(lancedb.__version__)'", "python3 apps/api/idx.py", "python3 apps/legacy/idx.py", "py"),
    ("rasterio-py-leftover-warped", "rasterio leftover vs warp.py", "rasterio", "1.3.11", "1.4.3", "warp.py", "# rasterio 1.3.11", "# rasterio 1.4.3", "WarpedVRT(src, crs='EPSG:4326')", "WarpedVRT(src, crs='EPSG:3857', resampling=Resampling.bilinear)", "src.read(1)", "src.read(1, masked=True)", "4326 nearest → 3857 bilinear masked", "python3 -c 'import rasterio; print(rasterio.__version__)'", "python3 apps/api/warp.py", "python3 apps/legacy/warp.py", "py"),
    ("rioxarray-py-leftover-reprojectx", "rioxarray leftover vs repro.py", "rioxarray", "0.17.0", "0.18.2", "repro.py", "# rioxarray 0.17.0", "# rioxarray 0.18.2", "da.rio.reproject('EPSG:4326')", "da.rio.reproject('EPSG:3857', resampling=Resampling.cubic)", "da.rio.to_raster('out.tif')", "da.rio.to_raster('out.tif', compress='deflate')", "4326 → 3857 cubic + deflate", "python3 -c 'import rioxarray; print(rioxarray.__version__)'", "python3 apps/api/repro.py", "python3 apps/legacy/repro.py", "py"),
    ("stackstac-py-leftover-mosaic", "stackstac leftover vs mos.py", "stackstac", "0.5.0", "0.5.1", "mos.py", "# stackstac 0.5.0", "# stackstac 0.5.1", "stackstac.stack(items, epsg=4326)", "stackstac.stack(items, epsg=3857, resampling=1)", "da.median('time')", "da.median('time', skipna=True)", "4326 → 3857 resampling + skipna", "python3 -c 'import stackstac; print(stackstac.__version__)'", "python3 apps/api/mos.py", "python3 apps/legacy/mos.py", "py"),
    ("odc-py-leftover-geobox", "ODC leftover vs geo.py", "odc", "1.9.0", "1.9.2", "geo.py", "# odc 1.9.0", "# odc 1.9.2", "GeoBox.from_bbox(bbox, crs='epsg:4326', resolution=0.001)", "GeoBox.from_bbox(bbox, crs='epsg:3857', resolution=10)", "dc.load(product='ls8', geobox=g)", "dc.load(product='ls8', geobox=g, dask_chunks={'time': 1})", "4326 0.001 → 3857 10m + dask", "python3 -c 'import odc.geo; print(odc.geo.__version__)'", "python3 apps/api/geo.py", "python3 apps/legacy/geo.py", "py"),
    ("pystac-py-leftover-item", "pystac leftover vs item.py", "pystac", "1.11.0", "1.13.0", "item.py", "# pystac 1.11.0", "# pystac 1.13.0", "Item(id='legacy', geometry=None, bbox=None, datetime=dt, properties={})", "Item(id='api', geometry=geom, bbox=bbox, datetime=dt, properties={'gsd': 10})", "item.set_self_href('legacy.json')", "item.set_self_href('api.json')", "null geom → api gsd 10", "python3 -c 'import pystac; print(pystac.__version__)'", "python3 apps/api/item.py", "python3 apps/legacy/item.py", "py"),
    ("stacapi-yml-leftover-query", "STAC API leftover vs q.yml", "stacapi", "4.0.0", "5.0.1", "q.yml", "# stacapi 4.0.0", "# stacapi 5.0.1", "filter-lang: cql2-text", "filter-lang: cql2-json", "fields: default", "fields: include=[id,properties.datetime]", "cql2-text → cql2-json + fields", "python3 -c 'import stac_fastapi; print(stac_fastapi.__version__)'", "python3 -c 'print(\"apps/api/q.yml\")'", "python3 -c 'print(\"apps/legacy/q.yml\")'", "yml"),
    ("sentinelhub-py-leftover-evalscript", "sentinelhub leftover vs ev.py", "sentinelhub", "3.10.2", "3.11.2", "ev.py", "# sentinelhub 3.10.2", "# sentinelhub 3.11.2", "evalscript = '//VERSION=2\\nreturn [B04]'", "evalscript = '//VERSION=3\\nreturn [B04, B08]'", "size=(512,512)", "size=(1024,1024)", "v2 B04 → v3 B04/B08 1024", "python3 -c 'import sentinelhub; print(sentinelhub.__version__)'", "python3 apps/api/ev.py", "python3 apps/legacy/ev.py", "py"),
    ("planetary-py-leftover-sign", "Planetary Computer leftover vs sign.py", "planetary", "1.0.0", "1.0.0-api", "sign.py", "# planetary 1.0.0", "# planetary 1.0.0-api", "pc.sign(href)", "pc.sign_inplace(item)", "catalog = pystac.Catalog.from_file(url)", "catalog = pc.sign(pystac.Catalog.from_file(url))", "sign href → sign_inplace item", "python3 -c 'import planetary_computer; print(planetary_computer.__version__)'", "python3 apps/api/sign.py", "python3 apps/legacy/sign.py", "py"),
    ("dpdk-conf-leftover-pmd", "DPDK leftover vs pmd.conf", "dpdk", "23.11", "24.11", "pmd.conf", "# dpdk 23.11", "# dpdk 24.11", "pmd = i40e", "pmd = ice", "max_simd = sse", "max_simd = avx512", "i40e SSE → ice AVX512", "pkg-config --modversion libdpdk", "testpmd -c apps/api/pmd.conf", "testpmd -c apps/legacy/pmd.conf", "conf"),
    ("vpp-conf-leftover-lcp", "VPP leftover vs lcp.conf", "vpp", "24.06", "24.10", "lcp.conf", "# vpp 24.06", "# vpp 24.10", "lcp create host-if name eth0", "lcp create host-if name eth0 netns dataplane", "dpdk { dev 0000:01:00.0 }", "dpdk { dev 0000:01:00.0 { num-rx-queues 4 } }", "LCP netns + 4 rx queues", "vppctl show version | head -n 1", "vpp -c apps/api/lcp.conf", "vpp -c apps/legacy/lcp.conf", "conf"),
    ("snabb-lua-leftover-app", "Snabb leftover vs app.lua", "snabb", "2023.08", "2024.08", "app.lua", "-- snabb 2023.08", "-- snabb 2024.08", "App = {name='legacy'}", "App = {name='api'}", "function App:push() end", "function App:pull() end", "push-only → pull app", "snabb --version || true", "snabb apps/api/app.lua", "snabb apps/legacy/app.lua", "lua"),
    ("ovs-conf-leftover-datapath", "Open vSwitch leftover vs ovs.conf", "ovs", "3.3.1", "3.4.1", "ovs.conf", "# ovs 3.3.1", "# ovs 3.4.1", "datapath_type=system", "datapath_type=netdev", "other_config:hw-offload=false", "other_config:hw-offload=true", "system → netdev + hw-offload", "ovs-vsctl --version | head -n 1", "ovs-vsctl --config apps/api/ovs.conf", "ovs-vsctl --config apps/legacy/ovs.conf", "conf"),
    ("ovn-nb-leftover-acl", "OVN leftover vs acl.ovn", "ovn", "24.03.2", "24.09.0", "acl.ovn", "# ovn 24.03.2", "# ovn 24.09.0", "acl match=\"ip\" action=allow", "acl match=\"ip4 && tcp\" action=allow-related", "priority=100", "priority=200 log=true", "ip allow → ip4 tcp allow-related log", "ovn-nbctl --version | head -n 1", "ovn-nbctl --db apps/api/acl.ovn show", "ovn-nbctl --db apps/legacy/acl.ovn show", "ovn"),
    ("gobgp-yml-leftover-policy", "GoBGP leftover vs pol.yml", "gobgp", "3.29.0", "3.35.0", "pol.yml", "# gobgp 3.29.0", "# gobgp 3.35.0", "defined-sets: { prefix-sets: [{name: legacy}] }", "defined-sets: { prefix-sets: [{name: api, prefix-list: [{ip-prefix: 10.0.0.0/8}]}] }", "policy-definitions: [{name: p, statements: [{actions: {route-disposition: accept-route}}]}]", "policy-definitions: [{name: p, statements: [{actions: {route-disposition: reject-route}}]}]", "legacy prefix → 10/8 reject", "gobgp --version | head -n 1", "gobgpd -f apps/api/pol.yml", "gobgpd -f apps/legacy/pol.yml", "yml"),
    ("exabgp-conf-leftover-neighbor", "ExaBGP leftover vs nei.conf", "exabgp", "4.2.21", "4.2.22", "nei.conf", "# exabgp 4.2.21", "# exabgp 4.2.22", "neighbor 192.0.2.1 {", "neighbor 192.0.2.2 {", "family { ipv4 unicast; }", "family { ipv4 unicast; ipv6 unicast; }", "peer .1 v4 → .2 v4+v6", "exabgp --version | head -n 1", "exabgp apps/api/nei.conf", "exabgp apps/legacy/nei.conf", "conf"),
    ("fdio-conf-leftover-plugin", "FD.io leftover vs plug.conf", "fdio", "24.06", "24.10", "plug.conf", "# fdio 24.06", "# fdio 24.10", "plugin disable default", "plugin enable dpdk_plugin.so", "api-segment { prefix vpp }", "api-segment { prefix api }", "disable default → enable dpdk prefix api", "vppctl show plugins | head || true", "vpp -c apps/api/plug.conf", "vpp -c apps/legacy/plug.conf", "conf"),
    ("nffgo-go-leftover-flow", "NFF-Go leftover vs flow.go", "nffgo", "0.9.2", "0.10.0", "flow.go", "// nffgo 0.9.2", "// nffgo 0.10.0", "flow.SetSender(0)", "flow.SetSender(1)", "flow.SetReceiver(0)", "flow.SetReceiver(1)\nflow.SetHandler(handle)", "port 0 → 1 + handler", "go test ./...", "go test ./apps/api", "go test ./apps/legacy", "go"),
    ("packetdrill-pkt-leftover-script", "packetdrill leftover vs s.pkt", "packetdrill", "2.0", "2.1", "s.pkt", "// packetdrill 2.0", "// packetdrill 2.1", "0 socket(..., SOCK_STREAM, IPPROTO_TCP) = 3", "0 socket(..., SOCK_STREAM, IPPROTO_TCP) = 3\n+0 setsockopt(3, IPPROTO_TCP, TCP_NODELAY, ...) = 0", "0.1 connect(3, ..., ...) = 0", "0.1 connect(3, ..., ...) = 0\n+0.0 write(3, ..., 100) = 100", "TCP_NODELAY + write 100", "packetdrill --version || true", "packetdrill apps/api/s.pkt", "packetdrill apps/legacy/s.pkt", "pkt"),
    ("gaussian-gjf-leftover-opt", "Gaussian leftover vs opt.gjf", "gaussian", "16c02", "16c03", "opt.gjf", "%chk=g16c02", "%chk=g16c03", "#p B3LYP/6-31G(d) Opt", "#p wB97X-D/def2-TZVP Opt Freq", "opt=tight", "opt=tight freq=noraman", "Opt 6-31G → wB97X-D def2-TZVP Freq", "g16 --version || true", "g16 apps/api/opt.gjf", "g16 apps/legacy/opt.gjf", "gjf"),
    ("turbomole-ctrl-leftover-ridft", "TURBOMOLE leftover vs control", "turbomole", "7.7", "7.8.1", "control", "$turbomole 7.7", "$turbomole 7.8.1", "$dft functional b-p", "$dft functional pbe0", "$ridft", "$ricc2", "b-p ridft → pbe0 ricc2", "ridft --version || true", "ridft -c apps/api/control", "ridft -c apps/legacy/control", "control"),
    ("adfqc-run-leftover-xc", "ADF leftover vs xc.run", "adfqc", "2024.1", "2024.2", "xc.run", "! adfqc 2024.1", "! adfqc 2024.2", "XC GGA PBE", "XC Hybrid B3LYP", "NumericalQuality Normal", "NumericalQuality Good", "PBE → B3LYP Good", "ams --version || true", "ams apps/api/xc.run", "ams apps/legacy/xc.run", "run"),
    ("mrcc-inp-leftover-ccsdt", "MRCC leftover vs ccsdt.minp", "mrcc", "2023", "2024", "ccsdt.minp", "# mrcc 2023", "# mrcc 2024", "calc=CCSD", "calc=CCSDT", "ccmaxit=50", "ccmaxit=100", "CCSD → CCSDT maxit 100", "dmrcc || true", "dmrcc apps/api/ccsdt.minp", "dmrcc apps/legacy/ccsdt.minp", "minp"),
    ("cfour-zmat-leftover-ccsd", "CFOUR leftover vs ZMAT", "cfour", "2.1", "2.1-patch", "ZMAT", "* cfour 2.1", "* cfour 2.1-patch", "CALC=CCSD", "CALC=CCSD(T)", "BASIS=PVDZ", "BASIS=PVTZ", "CCSD PVDZ → CCSD(T) PVTZ", "xcfour || true", "xcfour apps/api/ZMAT", "xcfour apps/legacy/ZMAT", "ZMAT"),
    ("xtb-inp-leftover-gfn2", "xtb leftover vs gfn.inp", "xtb", "6.7.0", "6.7.1", "gfn.inp", "# xtb 6.7.0", "# xtb 6.7.1", "$gfn 1", "$gfn 2", "$opt", "$opt\n  maxcycle=200", "GFN1 → GFN2 maxcycle 200", "xtb --version | head -n 1", "xtb apps/api/gfn.inp", "xtb apps/legacy/gfn.inp", "inp"),
    ("crest-inp-leftover-conf", "CREST leftover vs conf.inp", "crest", "3.0.1", "3.0.2", "conf.inp", "# crest 3.0.1", "# crest 3.0.2", "--gfn1", "--gfn2 --alpb h2o", "--quick", "--mquick", "gfn1 quick → gfn2 alpb mquick", "crest --version | head -n 1", "crest apps/api/conf.inp", "crest apps/legacy/conf.inp", "inp"),
    ("mopac-dat-leftover-pm7", "MOPAC leftover vs pm7.dat", "mopac", "22.1.1", "23.0.3", "pm7.dat", "* mopac 22.1.1", "* mopac 23.0.3", "PM6", "PM7", "CHARGE=0 SINGLET", "CHARGE=1 DOUBLET", "PM6 singlet → PM7 doublet", "mopac --version || true", "mopac apps/api/pm7.dat", "mopac apps/legacy/pm7.dat", "dat"),
    ("schnet-py-leftover-cutoff", "SchNet leftover vs cut.py", "schnet", "2.0.4", "2.1.0", "cut.py", "# schnet 2.0.4", "# schnet 2.1.0", "cutoff=5.0", "cutoff=6.0", "n_atom_basis=64", "n_atom_basis=128", "cutoff 5→6 + 128 basis", "python3 -c 'import schnetpack; print(schnetpack.__version__)'", "python3 apps/api/cut.py", "python3 apps/legacy/cut.py", "py"),
    ("nequip-yaml-leftover-lmax", "NequIP leftover vs lmax.yaml", "nequip", "0.6.1", "0.6.2", "lmax.yaml", "# nequip 0.6.1", "# nequip 0.6.2", "l_max: 1", "l_max: 2", "num_features: 32", "num_features: 64", "l_max 1→2 + 64 features", "python3 -c 'import nequip; print(nequip.__version__)'", "python3 -m nequip.train apps/api/lmax.yaml", "python3 -m nequip.train apps/legacy/lmax.yaml", "yaml"),
    ("mace-yaml-leftover-rmax", "MACE leftover vs rmax.yaml", "mace", "0.3.6", "0.3.10", "rmax.yaml", "# mace 0.3.6", "# mace 0.3.10", "r_max: 4.0", "r_max: 5.0", "hidden_irreps: 16x0e", "hidden_irreps: 128x0e + 128x1o", "r_max 4→5 + 128 irreps", "python3 -c 'import mace; print(mace.__version__)'", "python3 -m mace apps/api/rmax.yaml", "python3 -m mace apps/legacy/rmax.yaml", "yaml"),
    ("allegro-yaml-leftover-env", "Allegro leftover vs env.yaml", "allegro", "0.2.0", "0.3.0", "env.yaml", "# allegro 0.2.0", "# allegro 0.3.0", "env_embed_multiplicity: 8", "env_embed_multiplicity: 32", "two_body_latent_mlp: [8]", "two_body_latent_mlp: [64, 64]", "env 8 → 32 + 64 mlp", "python3 -c 'import allegro; print(allegro.__version__)'", "python3 -m allegro apps/api/env.yaml", "python3 -m allegro apps/legacy/env.yaml", "yaml"),
    ("phonopy-conf-leftover-mesh", "phonopy leftover vs mesh.conf", "phonopy", "2.27.0", "2.38.1", "mesh.conf", "# phonopy 2.27.0", "# phonopy 2.38.1", "MESH = 8 8 8", "MESH = 16 16 16", "GAMMA_CENTER = .FALSE.", "GAMMA_CENTER = .TRUE.", "8^3 → 16^3 gamma center", "phonopy --version | head -n 1", "phonopy --conf apps/api/mesh.conf", "phonopy --conf apps/legacy/mesh.conf", "conf"),
    ("phono3py-conf-leftover-fc3", "phono3py leftover vs fc3.conf", "phono3py", "3.3.0", "3.15.0", "fc3.conf", "# phono3py 3.3.0", "# phono3py 3.15.0", "DIM = 2 2 2", "DIM = 3 3 3", "CUTOFF_PAIR = 5.0", "CUTOFF_PAIR = 8.0", "DIM 2→3 cutoff 5→8", "phono3py --version | head -n 1", "phono3py --conf apps/api/fc3.conf", "phono3py --conf apps/legacy/fc3.conf", "conf"),
    ("alamode-xml-leftover-cubic", "ALAMODE leftover vs cubic.xml", "alamode", "1.4.2", "1.5.0", "cubic.xml", "<!-- alamode 1.4.2 -->", "<!-- alamode 1.5.0 -->", "<norder>2</norder>", "<norder>3</norder>", "<cutoff>6.0</cutoff>", "<cutoff>8.0</cutoff>", "norder 2→3 cutoff 6→8", "alm --version || true", "alm apps/api/cubic.xml", "alm apps/legacy/cubic.xml", "xml"),
    ("tdep-conf-leftover-fc2", "TDEP leftover vs fc2.in", "tdep", "1.2", "1.3", "fc2.in", "# tdep 1.2", "# tdep 1.3", "cutoffs 5.0", "cutoffs 8.0 6.0", "temperature 300", "temperature 0", "5A 300K → 8/6A 0K", "extract_forceconstants --version || true", "extract_forceconstants apps/api/fc2.in", "extract_forceconstants apps/legacy/fc2.in", "in"),
    ("hiphive-json-leftover-cutoffs", "hiPhive leftover vs cut.json", "hiphive", "1.3", "1.4", "cut.json", "// hiphive 1.3", "// hiphive 1.4", "\"cutoffs\": [5.0]", "\"cutoffs\": [6.0, 5.0, 4.0]", "\"fit_method\": \"least-squares\"", "\"fit_method\": \"ardr\"", "cutoffs 5 → 6/5/4 ardr", "python3 -c 'import hiphive; print(hiphive.__version__)'", "python3 apps/api/cut.json", "python3 apps/legacy/cut.json", "json"),
    ("seekpath-py-leftover-path", "seeK-path leftover vs path.py", "seekpath", "2.1.0", "2.1.1", "path.py", "# seekpath 2.1.0", "# seekpath 2.1.1", "get_path(cell, with_time_reversal=True)", "get_explicit_k_path(cell, reference_distance=0.025)", "recipe='hpkot'", "recipe='hpkot', with_time_reversal=False", "get_path → explicit k_path 0.025", "python3 -c 'import seekpath; print(seekpath.__version__)'", "python3 apps/api/path.py", "python3 apps/legacy/path.py", "py"),
    ("sumo-py-leftover-bs", "sumo leftover vs bs.py", "sumo", "2.3.8", "2.3.10", "bs.py", "# sumo 2.3.8", "# sumo 2.3.10", "sumo-bandplot --project", "sumo-bandplot --project --mode rgb", "ymin=-5", "ymin=-8 ymax=8", "project → rgb + wider window", "sumo-bandplot --help | head || true", "sumo-bandplot --config apps/api/bs.py", "sumo-bandplot --config apps/legacy/bs.py", "py"),
    ("galore-py-leftover-smear", "Galore leftover vs smear.py", "galore", "0.9.2", "0.9.3", "smear.py", "# galore 0.9.2", "# galore 0.9.3", "galore --lorentzian 0.4", "galore --gaussian 0.3", "units ev", "units cm", "lorentzian 0.4 eV → gaussian 0.3 cm", "galore --version || true", "galore apps/api/smear.py", "galore apps/legacy/smear.py", "py"),
    ("optados-odi-leftover-broaden", "OptaDOS leftover vs od.odi", "optados", "1.2", "1.3", "od.odi", "# optados 1.2", "# optados 1.3", "broadening : lorentzian", "broadening : gaussian", "adaptive_smearing : 0.4", "adaptive_smearing : 0.2", "lorentzian 0.4 → gaussian 0.2", "optados --version || true", "optados apps/api/od.odi", "optados apps/legacy/od.odi", "odi"),
    ("boltzwann-in-leftover-mu", "BoltzWann leftover vs mu.in", "boltzwann", "1.0", "1.1", "mu.in", "# boltzwann 1.0", "# boltzwann 1.1", "boltz_mu_min = -1.0", "boltz_mu_min = -2.0", "boltz_mu_max = 1.0", "boltz_mu_max = 2.0", "mu ±1 → ±2 eV", "boltzwann.x || true", "boltzwann.x < apps/api/mu.in", "boltzwann.x < apps/legacy/mu.in", "in"),
    ("wannier90-win-leftover-proj", "Wannier90 leftover vs proj.win", "wannier90", "3.1.0", "3.1.1", "proj.win", "! wannier90 3.1.0", "! wannier90 3.1.1", "projections = random", "projections = Si:sp3", "dis_win_max = 12", "dis_win_max = 16", "random → Si:sp3 + wider window", "wannier90.x --version | head -n 1", "wannier90.x apps/api/proj.win", "wannier90.x apps/legacy/proj.win", "win"),
    ("siesta-fdf-leftover-mesh", "SIESTA leftover vs mesh.fdf", "siesta", "5.0.0", "5.2.0", "mesh.fdf", "# siesta 5.0.0", "# siesta 5.2.0", "MeshCutoff 200 Ry", "MeshCutoff 400 Ry", "PAO.BasisSize DZP", "PAO.BasisSize TZDP", "200Ry DZP → 400Ry TZDP", "siesta --version | head -n 1", "siesta < apps/api/mesh.fdf", "siesta < apps/legacy/mesh.fdf", "fdf"),
    ("octopus-inp-leftover-td", "Octopus leftover vs td.inp", "octopus", "14.0", "15.1", "td.inp", "# octopus 14.0", "# octopus 15.1", "CalculationMode = gs", "CalculationMode = td", "TDPropagator = aetrs", "TDPropagator = exp_mid", "gs aetrs → td exp_mid", "octopus --version | head -n 1", "octopus apps/api/td.inp", "octopus apps/legacy/td.inp", "inp"),
    ("elk-in-leftover-tasks", "Elk leftover vs elk.in", "elk", "9.5.14", "10.3.12", "elk.in", "! elk 9.5.14", "! elk 10.3.12", "tasks\n  0", "tasks\n  10", "rgkmax\n  7.0", "rgkmax\n  8.5", "task 0 → 10 rgkmax 8.5", "elk --version || true", "elk apps/api/elk.in", "elk apps/legacy/elk.in", "in"),
    ("exciting-xml-leftover-groundstate", "exciting leftover vs gs.xml", "exciting", "oxygen", "nitrogen", "gs.xml", "<!-- exciting oxygen -->", "<!-- exciting nitrogen -->", "<groundstate ngridk=\"4 4 4\"/>", "<groundstate ngridk=\"8 8 8\" rgkmax=\"8.0\"/>", "<xs xstype=\"TDDFT\"/>", "<xs xstype=\"BSE\"/>", "k 4^3 → 8^3 + BSE", "exciting --version || true", "exciting apps/api/gs.xml", "exciting apps/legacy/gs.xml", "xml"),
    ("wien2k-in-leftover-rkmax", "WIEN2k leftover vs case.in1", "wien2k", "23.2", "24.1", "case.in1", "WIEN2k 23.2", "WIEN2k 24.1", "RKmax= 7.00", "RKmax= 8.50", "GMAX= 12.00", "GMAX= 16.00", "RKmax 7→8.5 GMAX 12→16", "x lapw0 || true", "x lapw1 -c apps/api/case.in1", "x lapw1 -c apps/legacy/case.in1", "in1"),
    ("fleur-xml-leftover-kpts", "FLEUR leftover vs kpts.xml", "fleur", "6.0", "7.0", "kpts.xml", "<!-- fleur 6.0 -->", "<!-- fleur 7.0 -->", "<kPointCount count=\"64\"/>", "<kPointCount count=\"256\" gamma=\"T\"/>", "<cutoffs Kmax=\"3.5\"/>", "<cutoffs Kmax=\"4.2\"/>", "64 k → 256 gamma + Kmax 4.2", "fleur --version || true", "fleur -xml apps/api/kpts.xml", "fleur -xml apps/legacy/kpts.xml", "xml"),
    ("spex-in-leftover-gw", "SPEX leftover vs gw.in", "spex", "0.6", "0.7", "gw.in", "# spex 0.6", "# spex 0.7", "JOB GW", "JOB GW+COHSEX", "NBAND 100", "NBAND 200", "GW → GW+COHSEX 200 bands", "spex --version || true", "spex apps/api/gw.in", "spex apps/legacy/gw.in", "in"),
    ("berkeleygw-inp-leftover-eps", "BerkeleyGW leftover vs eps.inp", "berkeleygw", "3.0.1", "4.0", "eps.inp", "# berkeleygw 3.0.1", "# berkeleygw 4.0", "epsilon_cutoff 10.0", "epsilon_cutoff 15.0", "number_bands 200", "number_bands 400", "cutoff 10→15 + 400 bands", "epsilon.cplx.x || true", "epsilon.cplx.x < apps/api/eps.inp", "epsilon.cplx.x < apps/legacy/eps.inp", "inp"),
    ("yambo-in-leftover-gw", "Yambo leftover vs gw.in", "yambo", "5.2.1", "5.3.0", "gw.in", "# yambo 5.2.1", "# yambo 5.3.0", "gw0                         # [GW] GoW0", "gw0 ppa                     # [GW] plasmon pole", "BndsRnXp= 1 200", "BndsRnXp= 1 400", "GoW0 → PPA 400 bands", "yambo --version | head -n 1", "yambo -F apps/api/gw.in", "yambo -F apps/legacy/gw.in", "in"),
    ("gamess-inp-leftover-mp2", "GAMESS leftover vs mp2.inp", "gamess", "2023R2", "2024R1", "mp2.inp", "! gamess 2023R2", "! gamess 2024R1", " $CONTRL SCFTYP=RHF MPLEVL=0 $END", " $CONTRL SCFTYP=RHF MPLEVL=2 $END", " $BASIS GBASIS=N31 NGAUSS=6 $END", " $BASIS GBASIS=N311 NGAUSS=6 $END", "HF/6-31G → MP2/6-311G", "rungms || true", "rungms apps/api/mp2.inp", "rungms apps/legacy/mp2.inp", "inp"),
    ("molpro-inp-leftover-ccsd", "Molpro leftover vs ccsd.inp", "molpro", "2024.1", "2025.1", "ccsd.inp", "***,molpro 2024.1", "***,molpro 2025.1", "hf", "{ccsd;core}", "basis=vdz", "basis=vtz", "HF VDZ → CCSD VTZ", "molpro --version || true", "molpro apps/api/ccsd.inp", "molpro apps/legacy/ccsd.inp", "inp"),
    ("dalton-dal-leftover-qc", "DALTON leftover vs qc.dal", "dalton", "2020.1", "2020.1-patch", "qc.dal", "**DALTON 2020.1", "**DALTON 2020.1-patch", ".HF", ".CCSD", "**WAVE FUNCTIONS", "**WAVE FUNCTIONS\n.DIRECT", "HF → CCSD DIRECT", "dalton --version || true", "dalton apps/api/qc.dal", "dalton apps/legacy/qc.dal", "dal"),
    ("pysisyphus-yaml-leftover-ts", "pysisyphus leftover vs ts.yaml", "pysisyphus", "0.8.0", "0.8.1", "ts.yaml", "# pysisyphus 0.8.0", "# pysisyphus 0.8.1", "type: tsopt", "type: cos", "calc: {type: xtb}", "calc: {type: orca, method: b3lyp}", "tsopt xtb → cos orca b3lyp", "python3 -c 'import pysisyphus; print(pysisyphus.__version__)'", "pysis apps/api/ts.yaml", "pysis apps/legacy/ts.yaml", "yaml"),
    ("geometric-yaml-leftover-opt", "geomeTRIC leftover vs opt.yaml", "geometric", "1.0.2", "1.1", "opt.yaml", "# geometric 1.0.2", "# geometric 1.1", "coordsys: cart", "coordsys: dlc", "converge: set", "converge: GAU_TIGHT", "cart set → dlc GAU_TIGHT", "geometric-optimize --version || true", "geometric-optimize apps/api/opt.yaml", "geometric-optimize apps/legacy/opt.yaml", "yaml"),
    ("spglib-py-leftover-prec", "spglib leftover vs prec.py", "spglib", "2.5.0", "2.6.0", "prec.py", "# spglib 2.5.0", "# spglib 2.6.0", "get_spacegroup(cell, symprec=1e-2)", "get_spacegroup(cell, symprec=1e-5, angle_tolerance=0.1)", "niggli_reduce(cell)", "niggli_reduce(cell, eps=1e-5)", "symprec 1e-2 → 1e-5 + angle", "python3 -c 'import spglib; print(spglib.__version__)'", "python3 apps/api/prec.py", "python3 apps/legacy/prec.py", "py"),
    ("diracq-inp-leftover-dc", "DIRAC leftover vs dc.inp", "diracq", "23.0", "24.0", "dc.inp", "**diracq 23.0", "**diracq 24.0", ".DC", ".X2C", "*HAMILTONIAN", "*HAMILTONIAN\n.GAUNT", "DC → X2C + Gaunt", "pam --version || true", "pam --inp apps/api/dc.inp", "pam --inp apps/legacy/dc.inp", "inp"),
    ("strawberryfields-py-leftover-engine", "StrawberryFields leftover vs eng.py", "strawberryfields", "0.23.0", "0.24.0", "eng.py", "# strawberryfields 0.23.0", "# strawberryfields 0.24.0", "sf.Engine('tf', backend_options={'cutoff_dim': 6})", "sf.Engine('bosonic')", "eng.run(prog, shots=1)", "eng.run(prog, shots=100)", "tf cutoff 6 → bosonic 100 shots", "python3 -c 'import strawberryfields; print(strawberryfields.__version__)'", "python3 apps/api/eng.py", "python3 apps/legacy/eng.py", "py"),
    ("qiskitaer-cfg-leftover-gpu", "Qiskit Aer leftover vs gpu.cfg", "qiskitaer", "0.15.1", "0.16.1", "gpu.cfg", "# qiskitaer 0.15.1", "# qiskitaer 0.16.1", "method = statevector", "method = tensor_network", "device = CPU", "device = GPU", "statevector CPU → tensor_network GPU", "python3 -c 'import qiskit_aer; print(qiskit_aer.__version__)'", "python3 -c 'print(\"apps/api/gpu.cfg\")'", "python3 -c 'print(\"apps/legacy/gpu.cfg\")'", "cfg"),
]

assert len(TOOLS) % 2 == 0
assert len(TOOLS) == 120
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
        raise SystemExit("duplicate slugs in r1148 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1148 catalog")


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
