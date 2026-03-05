"""Configuration for the reasoning honesty evaluation tool."""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Evaluation run configuration."""

    # API settings
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    target_model: str = "claude-sonnet-4-5-20250929"
    classifier_model: str = "claude-haiku-4-5-20251001"
    temperature: float = 0.0
    variance_temperature: float = 0.7
    max_tokens: int = 2048

    # Execution settings
    variance_runs: int = 5
    inter_call_delay: float = 1.0  # seconds between API calls
    probes_file: str = "probes.json"

    # Output settings
    results_dir: str = "results"
    reports_dir: str = "reports"

    # Classification mode: "heuristic" or "llm"
    classification_mode: str = "heuristic"

    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required. "
                "Set it with: export ANTHROPIC_API_KEY=your-key-here"
            )
