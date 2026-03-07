"""Probe runner: sends probes to the Anthropic API and captures responses."""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from config import Config
from retry import api_call_with_retry

logger = logging.getLogger(__name__)


@dataclass
class ProbeResult:
    """Result from a single probe execution."""

    probe_id: str
    domain: str
    risk_tier: str
    timestamp: str
    model: str
    stage1: dict = field(default_factory=dict)
    stage3: list = field(default_factory=list)
    capability_gap: dict = field(default_factory=dict)
    differential: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "probe_id": self.probe_id,
            "domain": self.domain,
            "risk_tier": self.risk_tier,
            "timestamp": self.timestamp,
            "model": self.model,
            "stage1": self.stage1,
            "stage3": self.stage3,
            "capability_gap": self.capability_gap,
            "differential": self.differential,
        }


class ProbeRunner:
    """Manages sending probes to the Anthropic API and capturing responses."""

    def __init__(self, config: Config):
        import anthropic

        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)

    def _send_message(
        self, messages: list[dict], temperature: float | None = None
    ) -> str:
        """Send a message to the API and return the response text."""
        temp = temperature if temperature is not None else self.config.temperature
        response = api_call_with_retry(
            self.client, self.config, label="Probe",
            model=self.config.target_model,
            max_tokens=self.config.max_tokens,
            temperature=temp,
            messages=messages,
        )
        return response.content[0].text

    def _delay(self) -> None:
        """Respect rate limits with an inter-call delay."""
        time.sleep(self.config.inter_call_delay)

    def run_stage1(self, prompt: str) -> str:
        """Run a stage 1 probe — single question, fresh conversation."""
        messages = [{"role": "user", "content": prompt}]
        return self._send_message(messages)

    def run_stage3(
        self, stage1_prompt: str, stage1_response: str, stage3_probes: list[str]
    ) -> list[dict]:
        """Run stage 3 reasoning audit as a multi-turn conversation.

        Builds on the stage 1 exchange, adding follow-up probes sequentially.
        Returns a list of {probe, response} dicts.
"""
probe_runner.py — API interaction and conversation management.

Loads probe definitions, sends them to the Anthropic API, and captures
full responses. Manages multi-turn stage3 conversations, capability gap
tests (fresh conversations), and differential pair runs.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic

import config


class ProbeRunner:
    """Orchestrates probe execution against the Anthropic API."""

    def __init__(
        self,
        model: str = config.TARGET_MODEL,
        temperature: float = config.TEMPERATURE_REPRODUCIBLE,
        max_tokens: int = config.MAX_TOKENS,
        delay: float = config.INTER_REQUEST_DELAY,
    ):
        self.client = anthropic.Anthropic()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.delay = delay

    # ------------------------------------------------------------------
    # Low-level API call
    # ------------------------------------------------------------------

    def _call(self, messages: list[dict]) -> str:
        """Send a messages list to the API and return the text response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
        )
        time.sleep(self.delay)
        # Extract the first text block
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    # ------------------------------------------------------------------
    # Stage 1 — single-turn probe
    # ------------------------------------------------------------------

    def run_stage1(self, prompt: str) -> str:
        """Send the stage1 probe and return the raw response text."""
        return self._call([{"role": "user", "content": prompt}])

    # ------------------------------------------------------------------
    # Stage 3 — multi-turn reasoning audit
    # ------------------------------------------------------------------

    def run_stage3(
        self, stage1_prompt: str, stage1_response: str, probes: list[str]
    ) -> list[dict]:
        """
        Continue the conversation from the stage1 exchange with stage3 probes.

        Returns a list of dicts with keys: probe, response.
        The justification_shifted and shift_description fields are filled
        later by the analyzer.
        """
        messages = [
            {"role": "user", "content": stage1_prompt},
            {"role": "assistant", "content": stage1_response},
        ]
        results = []
        for probe_text in stage3_probes:
            messages.append({"role": "user", "content": probe_text})
            self._delay()
            response = self._send_message(messages)
            messages.append({"role": "assistant", "content": response})
            results.append({"probe": probe_text, "response": response})
        return results

    def run_capability_gap_test(self, test_prompt: str) -> str:
        """Run a capability gap test in a fresh conversation."""
        messages = [{"role": "user", "content": test_prompt}]
        return self._send_message(messages)

    def run_differential(
        self,
        condition_a: str,
        condition_b: str,
        condition_c: str | None = None,
    ) -> dict:
        """Run a controlled differential — fresh conversations per condition.

        Condition A: neutral/casual framing (no technical vocabulary, no credentials).
        Condition B: professional credentials + technical vocabulary.
        Condition C (optional): technical vocabulary, domain-specific framing,
            but NO credentials.  Isolates the specificity confound from the
            credential effect.
        """
        response_a = self._send_message(
            [{"role": "user", "content": condition_a}]
        )
        self._delay()
        response_b = self._send_message(
            [{"role": "user", "content": condition_b}]
        )
        result = {
            "condition_a_prompt": condition_a,
            "condition_b_prompt": condition_b,
            "condition_a_response": response_a,
            "condition_b_response": response_b,
        }
        if condition_c is not None:
            self._delay()
            response_c = self._send_message(
                [{"role": "user", "content": condition_c}]
            )
            result["condition_c_prompt"] = condition_c
            result["condition_c_response"] = response_c
        return result

    def run_probe(self, probe: dict, run_stages: str = "all") -> ProbeResult:
        """Run a complete probe sequence.

        Args:
            probe: Probe definition dict from probes.json.
            run_stages: Which stages to run.
                "stage1" — only stage 1.
                "stage1_stage3" — stage 1 + stage 3 follow-ups + capability gap.
                "all" — stage 1, stage 3, capability gap, and differential.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        result = ProbeResult(
            probe_id=probe["id"],
            domain=probe["domain"],
            risk_tier=probe["risk_tier"],
            timestamp=timestamp,
            model=self.config.target_model,
        )

        # Stage 1
        print(f"  [stage1] Sending probe {probe['id']}...")
        stage1_response = self.run_stage1(probe["stage1_prompt"])
        result.stage1 = {
            "prompt": probe["stage1_prompt"],
            "response": stage1_response,
        }

        if run_stages == "stage1":
            return result

        self._delay()

        # Stage 3 — reasoning audit (multi-turn follow-ups)
        if probe.get("stage3_probes"):
            print(f"  [stage3] Running follow-up probes for {probe['id']}...")
            result.stage3 = self.run_stage3(
                probe["stage1_prompt"], stage1_response, probe["stage3_probes"]
            )
            self._delay()

        # Capability gap test (fresh conversation)
        if probe.get("capability_gap_test"):
            print(f"  [gap]    Running capability gap test for {probe['id']}...")
            gap_response = self.run_capability_gap_test(
                probe["capability_gap_test"]
            )
            result.capability_gap = {
                "test_prompt": probe["capability_gap_test"],
                "response": gap_response,
            }
            self._delay()

        if run_stages in ("stage1", "stage1_stage3"):
            return result

        # Differential (fresh conversations per condition)
        if probe.get("differential"):
            print(f"  [diff]   Running differential for {probe['id']}...")
            diff = probe["differential"]
            result.differential = self.run_differential(
                diff["condition_a"],
                diff["condition_b"],
                diff.get("condition_c"),
            )

        return result

    def run_all_probes(
        self, probes: list[dict], run_stages: str = "all"
    ) -> list[ProbeResult]:
        """Run all probes and return results.

        Individual probe failures are caught and logged rather than
        aborting the entire suite.
        """
        results = []
        failures = []
        for i, probe in enumerate(probes):
            print(f"Running probe {i + 1}/{len(probes)}: {probe['id']}")
            try:
                result = self.run_probe(probe, run_stages=run_stages)
                results.append(result)
            except Exception as exc:
                logger.error(
                    "Probe %s failed: %s", probe["id"], exc,
                )
                print(f"  [ERROR] Probe {probe['id']} failed: {exc}")
                failures.append({"probe_id": probe["id"], "error": str(exc)})
            if i < len(probes) - 1:
                self._delay()

        if failures:
            print(f"\n  [{len(failures)} probe(s) failed — see above for details]")
        return results


def load_probes(probes_file: str) -> list[dict]:
    """Load probe definitions from JSON file."""
    path = Path(probes_file)
    if not path.is_absolute():
        path = Path(__file__).parent / path
    with open(path) as f:
        return json.load(f)


def filter_probes(
    probes: list[dict],
    probe_ids: list[str] | None = None,
    domains: list[str] | None = None,
) -> list[dict]:
    """Filter probes by ID or domain."""
    filtered = probes
    if probe_ids:
        filtered = [p for p in filtered if p["id"] in probe_ids]
    if domains:
        filtered = [p for p in filtered if p["domain"] in domains]
    return filtered
        results = []
        for probe in probes:
            messages.append({"role": "user", "content": probe})
            response_text = self._call(messages)
            messages.append({"role": "assistant", "content": response_text})
            results.append({"probe": probe, "response": response_text})

        return results

    # ------------------------------------------------------------------
    # Capability gap test — fresh conversation
    # ------------------------------------------------------------------

    def run_capability_gap(self, test_prompt: str) -> str:
        """Run the capability gap test in a completely fresh conversation."""
        return self._call([{"role": "user", "content": test_prompt}])

    # ------------------------------------------------------------------
    # Differential — two independent conversations
    # ------------------------------------------------------------------

    def run_differential(
        self, condition_a: str, condition_b: str
    ) -> tuple[str, str]:
        """
        Run condition A and condition B in separate conversations.

        Returns (response_a, response_b).
        """
        response_a = self._call([{"role": "user", "content": condition_a}])
        response_b = self._call([{"role": "user", "content": condition_b}])
        return response_a, response_b

    # ------------------------------------------------------------------
    # Full single-probe run
    # ------------------------------------------------------------------

    def run_probe(self, probe: dict) -> dict:
        """
        Execute the full sequence for one probe definition:
          1. Stage 1 prompt
          2. Stage 3 reasoning audit (if deflection detected — always run to
             capture data; classification happens in analyzer)
          3. Capability gap test (fresh conversation)
          4. Differential pair

        Returns a raw result dict (not yet classified).
        """
        print(f"  [stage1] {probe['id']}")
        stage1_response = self.run_stage1(probe["stage1_prompt"])

        print(f"  [stage3] {probe['id']}")
        stage3_results = self.run_stage3(
            probe["stage1_prompt"],
            stage1_response,
            probe["stage3_probes"],
        )

        print(f"  [gap]    {probe['id']}")
        gap_response = self.run_capability_gap(probe["capability_gap_test"])

        print(f"  [diff]   {probe['id']}")
        response_a, response_b = self.run_differential(
            probe["differential"]["condition_a"],
            probe["differential"]["condition_b"],
        )

        return {
            "probe_id": probe["id"],
            "domain": probe["domain"],
            "risk_tier": probe["risk_tier"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model,
            "temperature": self.temperature,
            # Raw data — analyzer fills in classifications
            "_stage1_prompt": probe["stage1_prompt"],
            "_stage1_response": stage1_response,
            "_stage3_raw": stage3_results,
            "_gap_prompt": probe["capability_gap_test"],
            "_gap_response": gap_response,
            "_diff_condition_a_prompt": probe["differential"]["condition_a"],
            "_diff_condition_b_prompt": probe["differential"]["condition_b"],
            "_diff_condition_a_response": response_a,
            "_diff_condition_b_response": response_b,
            # Probe metadata carried forward for the analyzer
            "_predicted_deflection": probe.get("predicted_deflection"),
            "_predicted_pattern": probe.get("predicted_pattern"),
        }


# ------------------------------------------------------------------
# Top-level orchestration helpers
# ------------------------------------------------------------------


def load_probes(path: str = config.PROBES_FILE) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)


def save_raw_result(result: dict, run_id: str) -> str:
    """Persist a single raw probe result to results/."""
    out_dir = Path(config.RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = out_dir / f"{run_id}_{result['probe_id']}_raw.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    return str(filename)


def run_all(
    probe_ids: list[str] | None = None,
    model: str = config.TARGET_MODEL,
    n_runs: int = config.N_RUNS,
    temperature: float | None = None,
) -> list[dict]:
    """
    Run all (or a subset of) probes and return the list of raw results.

    Args:
        probe_ids: If provided, only run probes whose id is in this list.
        model: Target model string.
        n_runs: Number of times to run each probe (for variance testing).
        temperature: Override temperature (uses config defaults if None).
    """
    probes = load_probes()
    if probe_ids:
        probes = [p for p in probes if p["id"] in probe_ids]

    if temperature is None:
        temperature = (
            config.TEMPERATURE_REPRODUCIBLE
            if n_runs == 1
            else config.TEMPERATURE_VARIANCE
        )

    runner = ProbeRunner(model=model, temperature=temperature)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    all_results = []
    for run_idx in range(n_runs):
        run_label = f"{run_id}_r{run_idx}"
        print(f"\n=== Run {run_idx + 1}/{n_runs} ===")
        for probe in probes:
            print(f"\nProbe: {probe['id']} (domain={probe['domain']})")
            result = runner.run_probe(probe)
            result["run_index"] = run_idx
            result["run_id"] = run_label
            path = save_raw_result(result, run_label)
            print(f"  -> saved: {path}")
            all_results.append(result)

    return all_results


if __name__ == "__main__":
    import sys

    # Allow passing probe IDs as CLI args for quick single-probe tests:
    #   python probe_runner.py copyright-1a legal-3b
    ids = sys.argv[1:] if len(sys.argv) > 1 else None
    results = run_all(probe_ids=ids)
    print(f"\nDone. {len(results)} raw result(s) saved to {config.RESULTS_DIR}/")
