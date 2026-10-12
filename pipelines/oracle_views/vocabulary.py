"""Vocabulary of the oracle-grounded text training view (the five neuromorphic families).

The family names, the row shapes, the public allowlist each family's prompt is
projected from, the closed label vocabulary each family's completion and
multiple-choice answer are drawn from, the prompt sections and per-family
instructions, every leak and refusal code as a declared constant, and the coded
refusal type on the shared ``refusals.CodedRefusal``. No logic beyond the
refusal helpers.

The view is a projection of accepted, publishable, simulated measurements into
text. Nothing here claims training readiness, a registry row, a rights lane or
a completed round; those remain the factory's own gates.
"""

from __future__ import annotations

from ._contract import bind_import_twin
from ._contract import families as _families
from ._contract import refusals as _refusals

VIEW_FORMAT = "oracle-text-views/1"
SUMMARY_FILENAME = "VIEWS.json"

ENCODER_FAMILY = _families.ENCODER_FAMILY
NEURON_FAMILY = _families.NEURON_FAMILY
MESH_FAMILY = _families.MESH_FAMILY
CREDIT_FAMILY = _families.CREDIT_FAMILY
MEMORY_FAMILY = _families.MEMORY_FAMILY
FAMILIES = tuple(_families.FAMILY_NAMES)
FAMILY_SET = frozenset(FAMILIES)

# What a positive example must carry; the only record fields the gate reads.
STATUS_ACCEPTED = "accepted"
PROVENANCE_SIMULATED = "simulated"
PREDICTED_PREFIX = "predicted_"
CANDIDATE_TEXT_KEYS = ("basis",)

# The public allowlist: the only scenario and intervention keys a prompt is
# rendered from. ``question`` leads the prompt; the rest is the scenario block.
# A family without an intervention requires ``intervention`` to be null.
QUESTION_KEY = "question"
SCENARIO_KEYS = {
    ENCODER_FAMILY: (
        "encoding_pair", "perturbation", "sample_count", "sample_ms", "signal",
        "signal_family", "signal_parameters",
    ),
    NEURON_FAMILY: ("baseline_parameters", "dt_ms", "duration_ms", "stimulus"),
    MESH_FAMILY: ("duration_ms", "edges", "nodes", "sink", "source", "stimulus"),
    CREDIT_FAMILY: ("circuit", "outcome", "situation"),
    MEMORY_FAMILY: (
        "cue", "cue_ms", "delay_ms", "distractor_count", "distractor_ms", "event_sparsity",
        "network_variant", "probe_ms", "reset_ms",
    ),
}
INTERVENTION_KEYS = {
    ENCODER_FAMILY: None,
    NEURON_FAMILY: ("description", "factor", "operation", "parameter", "target"),
    MESH_FAMILY: ("description", "edge", "edge_index", "kind", "parameters"),
    CREDIT_FAMILY: None,
    MEMORY_FAMILY: None,
}

# Row shapes. A row carries exactly these keys and nothing else.
KIND_SFT = "sft"
KIND_CHAT = "chat"
KIND_CHOICE = "choice"
ROW_KINDS = (KIND_SFT, KIND_CHAT, KIND_CHOICE)
ROW_KEYS = {
    KIND_SFT: frozenset({"prompt", "completion"}),
    KIND_CHAT: frozenset({"messages"}),
    KIND_CHOICE: frozenset({"prompt", "options", "answer"}),
}
MESSAGE_KEYS = frozenset({"role", "content"})
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

# Public-view compaction: a numeric array longer than this is replaced by a
# deterministic summary (length, min, max, mean at canonical precision).
MAX_INLINE_VALUES = 8
SUMMARY_MARKER = "summarized"

# Closed label vocabularies, one per family. The completion is a JSON object
# over these values plus the measured scalars named in INSTRUCTIONS; the
# multiple-choice answer is one option drawn from them.
ENCODER_BASES = ("information_retention", "spike_count_tiebreak", "tie")
ENCODER_TIE_OPTION = "tie"
NEURON_DIRECTIONS = ("increases_firing", "decreases_firing", "unchanged_firing")
MESH_SINK_NOT_REACHED = "sink_not_reached"
MESH_SINK_NEWLY_REACHED = "sink_newly_reached"
MESH_SINK_NO_LONGER_REACHED = "sink_no_longer_reached"
MESH_SINK_REACHED_EARLIER = "sink_reached_earlier"
MESH_SINK_REACHED_LATER = "sink_reached_later"
MESH_SINK_REACHED_UNCHANGED = "sink_reached_unchanged_delay"
MESH_OUTCOMES = (
    MESH_SINK_NOT_REACHED, MESH_SINK_NEWLY_REACHED, MESH_SINK_NO_LONGER_REACHED,
    MESH_SINK_REACHED_EARLIER, MESH_SINK_REACHED_LATER, MESH_SINK_REACHED_UNCHANGED,
)
CREDIT_VALENCES = ("positive", "negative", "neutral")
CREDIT_POTENTIATION = "potentiation"
CREDIT_DEPRESSION = "depression"
CREDIT_NO_CHANGE = "none"
CREDIT_WEIGHT_DIRECTIONS = (CREDIT_POTENTIATION, CREDIT_DEPRESSION, CREDIT_NO_CHANGE)
CREDIT_SYNAPSE_PREFIX = "synapse_"
CREDIT_NO_UPDATE = "no_update"
MEMORY_RESPONSES = ("A", "B", "none")

# The candidate guess each completion field or choice answer could be copied
# from; the leak check reports a label that disagrees with the measurement but
# equals the guess.
GUESS_FIELDS = {
    ENCODER_FAMILY: {"winner": "predicted_winner"},
    NEURON_FAMILY: {"direction": "predicted_direction"},
    MESH_FAMILY: {
        "sink_reached_after": "predicted_sink_reached",
        "propagation_delay_after_ms": "predicted_propagation_delay_ms",
    },
    CREDIT_FAMILY: {
        "valence": "predicted_valence",
        "weight_direction": "predicted_weight_direction",
        "strongest_synapse": "predicted_strongest_synapse",
    },
    MEMORY_FAMILY: {"response": "predicted_response"},
}
CHOICE_FIELD = {
    ENCODER_FAMILY: "winner",
    NEURON_FAMILY: "direction",
    MESH_FAMILY: "outcome",
    CREDIT_FAMILY: "strongest_synapse",
    MEMORY_FAMILY: "response",
}

# Prompt text. The prompt is the question, the compact public view and the
# family's instruction; the choice variant swaps in the options and its question.
SCENARIO_HEADING = "### Scenario"
INTERVENTION_HEADING = "### Intervention"
OPTIONS_HEADING = "### Options"
INSTRUCTIONS_HEADING = "### Instructions"
CHOICE_INSTRUCTION = "Answer with exactly one of the options above, verbatim."
INSTRUCTIONS = {
    ENCODER_FAMILY: (
        'Reply with one JSON object {"winner": ..., "winner_basis": ...}: the encoding of the '
        "compared pair whose matched decoder preserves more of the trace (null on a tie), and "
        "whether that decision rests on information_retention, on a spike_count_tiebreak, or "
        "is a tie."
    ),
    NEURON_FAMILY: (
        'Reply with one JSON object {"direction": ..., "spike_count_after": ..., '
        '"spike_count_before": ...}: whether the intervention increases_firing, '
        "decreases_firing or leaves it unchanged_firing, with the spike counts after and "
        "before it."
    ),
    MESH_FAMILY: (
        'Reply with one JSON object {"outcome": ..., "propagation_delay_after_ms": ..., '
        '"propagation_delay_before_ms": ..., "sink_reached_after": ..., '
        '"sink_reached_before": ...}: the outcome as one of sink_not_reached, '
        "sink_newly_reached, sink_no_longer_reached, sink_reached_earlier, sink_reached_later "
        "or sink_reached_unchanged_delay, the source-to-sink propagation delay in milliseconds "
        "after and before the perturbation (null when unreached), and whether the sink is "
        "reached after and before it."
    ),
    CREDIT_FAMILY: (
        'Reply with one JSON object {"strongest_synapse": ..., "valence": ..., '
        '"weight_direction": ...}: the zero-based index of the synapse whose weight moves most '
        "(null when no update is applied), the modulator valence (positive, negative or "
        "neutral) and the net weight direction (potentiation, depression or none)."
    ),
    MEMORY_FAMILY: (
        'Reply with one JSON object {"distractor_invariant": ..., "response": ...}: whether '
        "shifting the distractors leaves the response unchanged (null when there are no "
        "distractors), and the output the network selects at the probe (A, B or none)."
    ),
}
CHOICE_QUESTIONS = {
    ENCODER_FAMILY: (
        "Which encoding's matched decoder preserves more of the trace? On near-equal "
        "retention the encoding that spends fewer spikes wins; answer tie when neither does."
    ),
    NEURON_FAMILY: "How does the intervention change the neuron's spike count?",
    MESH_FAMILY: "How does the perturbation change whether and when the sink is reached?",
    CREDIT_FAMILY: (
        "Which synapse's weight moves most under the reward-modulated update? Answer "
        "no_update when no update is applied."
    ),
    MEMORY_FAMILY: "Which output does the network select at the probe?",
}
PROJECTION_NOTE = (
    "A text projection of accepted, publishable, simulated oracle measurements. It asserts "
    "no training readiness, registry row, rights lane or completed round; the training audit, "
    "the compose contract and the round gate remain the factory's authorities."
)

# --- codes -----------------------------------------------------------------
# Leak checks over a rendered row (reported per row; the CLI writes nothing on any).
LEAK_VIEW_EXTRA_KEYS = "VIEW_EXTRA_KEYS"
LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW = "PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW"
LEAK_COMPLETION_NOT_FROM_MEASUREMENT = "COMPLETION_NOT_FROM_MEASUREMENT"
LEAK_LABEL_NOT_DERIVED_FROM_MEASUREMENT = "LABEL_NOT_DERIVED_FROM_MEASUREMENT"
LEAK_MEASUREMENT_DIGEST_MISMATCH = "MEASUREMENT_DIGEST_MISMATCH"
LEAK_PROPOSAL_DIGEST_MISMATCH = "PROPOSAL_DIGEST_MISMATCH"
LEAK_CANDIDATE_PREDICTION_LEAKED = "CANDIDATE_PREDICTION_LEAKED"
LEAK_HIDDEN_REASONING_KEY = "HIDDEN_REASONING_KEY"
LEAK_ROW_FROM_NON_POSITIVE_RECORD = "ROW_FROM_NON_POSITIVE_RECORD"
LEAK_CODES = (
    LEAK_VIEW_EXTRA_KEYS, LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
    LEAK_COMPLETION_NOT_FROM_MEASUREMENT, LEAK_LABEL_NOT_DERIVED_FROM_MEASUREMENT,
    LEAK_MEASUREMENT_DIGEST_MISMATCH, LEAK_PROPOSAL_DIGEST_MISMATCH,
    LEAK_CANDIDATE_PREDICTION_LEAKED, LEAK_HIDDEN_REASONING_KEY,
    LEAK_ROW_FROM_NON_POSITIVE_RECORD,
)
LEAK_CODE_SET = frozenset(LEAK_CODES)

# Refusals: coded refusals raised by the view's own entry points. The first
# four are per record (the CLI lists them in VIEWS.json and continues); the rest
# refuse the whole run.
FINDING_UNKNOWN_FAMILY = "UNKNOWN_FAMILY"
FINDING_UNSUPPORTED_RECORD_SHAPE = "UNSUPPORTED_RECORD_SHAPE"
FINDING_RECORD_NOT_SEALED = "RECORD_NOT_SEALED"
FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE = "RECORD_NOT_A_POSITIVE_EXAMPLE"
FINDING_RECORD_FAILS_VIEW_GATE = "RECORD_FAILS_VIEW_GATE"
FINDING_RUN_DIR_MISSING = "RUN_DIR_MISSING"
FINDING_RUN_NOT_AUTHENTICATED = "RUN_NOT_AUTHENTICATED"
FINDING_DESTINATION_EXISTS = "DESTINATION_EXISTS"
FINDING_DESTINATION_UNDER_RAW = "DESTINATION_UNDER_RAW"
FINDING_DESTINATION_INSIDE_RUN = "DESTINATION_INSIDE_RUN"
FINDING_DESTINATION_WRITE_FAILED = "DESTINATION_WRITE_FAILED"
RECORD_REFUSAL_CODES = (
    FINDING_UNKNOWN_FAMILY, FINDING_UNSUPPORTED_RECORD_SHAPE, FINDING_RECORD_NOT_SEALED,
    FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE,
)
FINDING_CODES = (
    *RECORD_REFUSAL_CODES, FINDING_RECORD_FAILS_VIEW_GATE, FINDING_RUN_DIR_MISSING,
    FINDING_RUN_NOT_AUTHENTICATED, FINDING_DESTINATION_EXISTS, FINDING_DESTINATION_UNDER_RAW,
    FINDING_DESTINATION_INSIDE_RUN, FINDING_DESTINATION_WRITE_FAILED,
)
FINDING_CODE_SET = frozenset(FINDING_CODES)


class TextViewRefusal(_refusals.CodedRefusal):
    """The view's coded refusal: a ``ContractError`` whose ``str`` is ``"CODE: prose"``."""

    CODES = FINDING_CODE_SET


refuse, refuse_when, refuse_first = _refusals.helpers(TextViewRefusal)
shown = _refusals.shown


bind_import_twin(__name__)
