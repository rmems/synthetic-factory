"""Local Ollama/vLLM and OpenRouter-distillable model-channel generators.

Each reviewed identity is a distinct provider/channel pair. Local output is
never conflated with hosted or OpenRouter output from the same vendor.
"""

__all__ = (
    "_contract source_policy openai_client ollama openrouter vllm generate cli"
).split()

from ._contract import bind_import_twin

bind_import_twin(__name__)
