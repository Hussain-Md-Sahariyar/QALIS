"""
QALIS Input Validation
======================

Validates CollectorConfig instances and raw interaction dicts before
metric collection begins. Raises ``ValueError`` with a descriptive
message on invalid input.

Paper reference: §3.3 — data collection protocol; §4.2 — metric preconditions.
"""

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Valid values
# ---------------------------------------------------------------------------
_VALID_DOMAINS = {
    "customer_support", "code_generation", "document_qa",
    "healthcare", "legal", "e_commerce", "general",
}
_VALID_RISK_LEVELS = {"low", "medium", "high"}
_VALID_LAYERS      = {1, 2, 3, 4}
_REQUIRED_INTERACTION_KEYS = {"query", "response"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_config(config) -> None:
    """
    Validate a CollectorConfig object.

    Raises:
        ValueError: If any field is invalid.
    """
    if not config.system_id or not isinstance(config.system_id, str):
        raise ValueError("CollectorConfig.system_id must be a non-empty string.")

    if config.risk_level not in _VALID_RISK_LEVELS:
        raise ValueError(
            f"CollectorConfig.risk_level must be one of {_VALID_RISK_LEVELS}, "
            f"got: {config.risk_level!r}"
        )

    invalid_layers = set(config.layers) - _VALID_LAYERS
    if invalid_layers:
        raise ValueError(
            f"CollectorConfig.layers contains invalid values: {invalid_layers}. "
            f"Must be subset of {_VALID_LAYERS}."
        )

    for dim, weight in config.dimension_weights.items():
        if not isinstance(weight, (int, float)) or weight < 0:
            raise ValueError(
                f"dimension_weights[{dim!r}] must be a non-negative number, got: {weight!r}"
            )


def validate_interaction(interaction: Dict[str, Any]) -> None:
    """
    Validate a single interaction dict before calling QALISCollector.collect().

    Raises:
        ValueError: If required keys are missing or values are invalid.
        TypeError:  If query or response are not strings.
    """
    missing = _REQUIRED_INTERACTION_KEYS - set(interaction.keys())
    if missing:
        raise ValueError(f"Interaction dict is missing required keys: {missing}")

    query    = interaction.get("query", "")
    response = interaction.get("response", "")

    if not isinstance(query, str):
        raise TypeError(f"'query' must be a str, got {type(query).__name__!r}")
    if not isinstance(response, str):
        raise TypeError(f"'response' must be a str, got {type(response).__name__!r}")
    if not query.strip():
        raise ValueError("'query' must not be empty or whitespace-only.")

    context = interaction.get("context")
    if context is not None:
        if not isinstance(context, list):
            raise TypeError(f"'context' must be a list of str, got {type(context).__name__!r}")
        for i, chunk in enumerate(context):
            if not isinstance(chunk, str):
                raise TypeError(f"'context[{i}]' must be a str, got {type(chunk).__name__!r}")

    latency = interaction.get("latency_ms")
    if latency is not None and (not isinstance(latency, (int, float)) or latency < 0):
        raise ValueError(f"'latency_ms' must be a non-negative number, got: {latency!r}")
