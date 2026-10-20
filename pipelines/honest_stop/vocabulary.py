"""Constants for the honest-stop family. The config file must match these pins."""

from __future__ import annotations

from ._contract import bind_import_twin

FAMILY = "agent-honest-stop-episode"
DATASET = "rmems/agent-honest-stop-episodes"
WORLD = "honest-stop-world-v1"
BUILDER_NAME = "honest-stop-scenario-v1"
BUILDER_ROLE = "scenario_builder"
WRITER_ROLE = "writer"
DEDUP_ROLE = "dedup"
WRITER_MODEL = "gemma4:12b"
DEDUP_MODEL = "qwen3-embedding:8b"
OLLAMA_URL = "http://127.0.0.1:11434"
SCHEMA_RELATIVE = "schemas/agent-honest-stop-episode-v1.schema.json"
FAMILY_SCHEMA = "agent-honest-stop-family-v1"
EXCLUSION_SCHEMA = "agent-honest-stop-exclusion-v1"
EXCLUSION_LIST = "held_out"
GATE_PROTOCOL = "honest-stop-gate/1"
GATE_MARKER = "HONEST-STOP-REPORT "
ACTION_TYPES = ("stop", "ask", "report_blocked")
SPLITS = ("train", "validation", "held_out")
HELD_OUT = "held_out"
MAX_RECORD_BYTES = 1024 * 1024
MAX_STEPS = 8
DEFAULT_TIMEOUT_S = 5.0
CODE_OK = "ok"

RECORD_KEYS = (
    "record_id",
    "family",
    "task",
    "context",
    "trajectory",
    "correct_action",
    "counterfactual_fake_success",
    "result",
    "provenance",
)
CONTEXT_KEYS = ("scenario_id", "seed", "task_id", "world")
STEP_KEYS = ("n", "tool_call", "observation")
TOOL_CALL_KEYS = ("name", "args")
ACTION_KEYS = ("type", "message")
RESULT_KEYS = ("verified_blocker",)
PROVENANCE_KEYS = ("produced_at", "actors", "lineage")
ACTOR_KEYS = ("role", "name", "digest")
LINEAGE_KEYS = (
    "scenario_id",
    "seed",
    "run_seed",
    "builder",
    "config_sha256",
    "parent_ids",
)

__all__ = [name for name in globals() if name.isupper()]


class FamilyError(Exception):
    """A coded refusal. ``code`` is the stable token; the message adds detail."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


bind_import_twin(__name__)
