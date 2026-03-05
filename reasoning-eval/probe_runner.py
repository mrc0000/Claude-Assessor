"""Probe runner: sends probes to the Anthropic API and captures responses."""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from config import Config


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
        response = self.client.messages.create(
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

    def run_differential(self, condition_a: str, condition_b: str) -> dict:
        """Run a controlled differential — two fresh conversations."""
        response_a = self._send_message(
            [{"role": "user", "content": condition_a}]
        )
        self._delay()
        response_b = self._send_message(
            [{"role": "user", "content": condition_b}]
        )
        return {
            "condition_a_prompt": condition_a,
            "condition_b_prompt": condition_b,
            "condition_a_response": response_a,
            "condition_b_response": response_b,
        }

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

        # Differential (two fresh conversations)
        if probe.get("differential"):
            print(f"  [diff]   Running differential for {probe['id']}...")
            diff = probe["differential"]
            result.differential = self.run_differential(
                diff["condition_a"], diff["condition_b"]
            )

        return result

    def run_all_probes(
        self, probes: list[dict], run_stages: str = "all"
    ) -> list[ProbeResult]:
        """Run all probes and return results."""
        results = []
        for i, probe in enumerate(probes):
            print(f"Running probe {i + 1}/{len(probes)}: {probe['id']}")
            result = self.run_probe(probe, run_stages=run_stages)
            results.append(result)
            if i < len(probes) - 1:
                self._delay()
        return results


def load_probes(probes_file: str) -> list[dict]:
    """Load probe definitions from JSON file."""
    path = Path(probes_file)
    if not path.is_absolute():
        path = Path(__file__).parent / path
    with open(path) as f:
        return json.load(f)
