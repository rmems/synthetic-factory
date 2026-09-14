#!/usr/bin/env python3
import glob
import json
import re

def tokenize(text):
    return {tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if tok}

def jaccard(a, b):
    sa, sb = tokenize(a), tokenize(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

ours = []
with open("/tmp/ttf-r71-live/batch-r71.jsonl") as f:
    for line in f:
        ours.append(json.loads(line))

paths = glob.glob("/tmp/ttf-r*/batch-r*.jsonl") + glob.glob(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/thalamic-trajectory-factory/batch-r*.jsonl"
)

hits = [p for p in paths if "scandium-fluoride-cell" in open(p, errors="ignore").read()]
print("scandium files", hits)

pairs = []
used = set()
for rec in ours:
    d = rec["state"]["description"]
    for p in paths:
        if "ttf-r71-live" in p:
            continue
        try:
            fh = open(p)
        except OSError:
            continue
        with fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                od = o.get("state", {}).get("description", "")
                dom = o.get("state", {}).get("domain")
                if dom:
                    used.add(dom)
                if not od:
                    continue
                j = jaccard(d, od)
                if j >= 0.28:
                    pairs.append((j, rec["id"], o.get("id"), p, od[:140]))

pairs.sort(reverse=True)
print("top collisions:")
for row in pairs[:20]:
    print(f"{row[0]:.3f} {row[1]} vs {row[2]} {row[3]}")
    print("   ", row[4])

cands = [
    "zinc-phosphide-sublimer",
    "gallium-arsenide-lpe",
    "hafnium-carbide-pvd",
    "tellurium-dioxide-melt",
    "niobium-carbide-sinter",
    "lithium-hexafluorophosphate-cell",
    "bismuth-vanadate-calciner",
    "lanthanum-hexaboride-sinter",
    "yttrium-fluoride-cell",
    "tungsten-oxytetrachloride-still",
    "molybdenum-hexacarbonyl-cvd",
    "samarium-cobalt-sinter",
    "cesium-iodide-bridgman",
    "platinum-hexafluoride-still",
]
for c in cands:
    print("CAND", c, "USED" if c in used else "free")
print("n used domains", len(used))
