"""Generator side of family 5: temporal-memory-spike-challenges.

Proposes a cue/delay/probe task over a latch network variant, with optional
distractors and a rare reset pulse. The response prediction assumes perfect
retention unless reset — it ignores the loop parameters entirely, so the
oracle's simulated network is the only authority on what actually survives.
"""


def propose_memory_scenario(rng):
    cue = rng.choice(("A", "B"))
    cue_ms = rng.uniform(15.0, 35.0)
    delay_ms = rng.choice((80.0, 150.0, 240.0, 360.0, 520.0, 700.0))
    probe_ms = cue_ms + delay_ms
    distractor_count = rng.randint(0, 4)
    distractors = (
        sorted(rng.uniform(cue_ms + 20.0, probe_ms - 15.0) for _ in range(distractor_count))
        if probe_ms - 15.0 > cue_ms + 20.0
        else []
    )
    reset_ms = None
    if rng.random() < 0.25 and probe_ms - 25.0 > cue_ms + 25.0:
        reset_ms = rng.uniform(cue_ms + 25.0, probe_ms - 25.0)
    network = {
        "loop_delay_ms": rng.choice((8.0, 10.0, 12.0, 14.0)),
        "latch_adaptation_b": rng.choice((0.015, 0.02, 0.03, 0.04, 0.055)),
        "distractor_weight": rng.choice((0.35, 0.45, 0.6, 1.1)),
    }
    return {
        "cue": cue,
        "cue_ms": cue_ms,
        "probe_ms": probe_ms,
        "delay_ms": delay_ms,
        "distractor_ms": distractors,
        "distractor_count": len(distractors),
        "reset_ms": reset_ms,
        "event_sparsity": (len(distractors) + 1) / max(1.0, delay_ms / 100.0),
        "network_variant": network,
        "question": (
            f"After a {delay_ms:.0f} ms delay with {len(distractors)} distractors"
            f"{' and a reset pulse' if reset_ms is not None else ''}, "
            "which output does the network select at the probe?"
        ),
    }


def predict_memory_response(scenario):
    """Assumes the cue survives unless it was explicitly reset."""
    if scenario["reset_ms"] is not None:
        predicted = "none"
    else:
        predicted = scenario["cue"]
    return {
        "kind": "non_authoritative_guess",
        "predicted_response": predicted,
        "basis": (
            "assumes perfect retention unless a reset pulse is present; "
            "makes no use of the loop parameters and runs no simulation"
        ),
    }
