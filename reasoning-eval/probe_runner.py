"""Probe runner: sends probes to the Anthropic API and captures responses."""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from config import Config

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
        """Send a message to the API and return the response text.

        Retries with exponential backoff on rate limit (429) and overloaded
        errors, up to config.max_retries attempts.
        """
        import anthropic

        temp = temperature if temperature is not None else self.config.temperature
        last_error: Exception | None = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.client.messages.create(
                    model=self.config.target_model,
                    max_tokens=self.config.max_tokens,
                    temperature=temp,
                    messages=messages,
                    timeout=self.config.api_timeout,
                )
                return response.content[0].text
            except anthropic.RateLimitError as exc:
                last_error = exc
                delay = self.config.retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Rate limited (429) on attempt %d/%d. "
                    "Retrying in %.1fs...",
                    attempt, self.config.max_retries, delay,
                )
                print(
                    f"  [retry] Rate limited, attempt {attempt}/{self.config.max_retries}. "
                    f"Waiting {delay:.0f}s..."
                )
                time.sleep(delay)
            except anthropic.APIStatusError as exc:
                if exc.status_code == 529 and self.config.retry_on_overload:
                    last_error = exc
                    delay = self.config.retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        "API overloaded (529) on attempt %d/%d. "
                        "Retrying in %.1fs...",
                        attempt, self.config.max_retries, delay,
                    )
                    print(
                        f"  [retry] API overloaded, attempt {attempt}/{self.config.max_retries}. "
                        f"Waiting {delay:.0f}s..."
                    )
                    time.sleep(delay)
                else:
                    raise
            except anthropic.APIConnectionError as exc:
                last_error = exc
                delay = self.config.retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Connection error on attempt %d/%d: %s. "
                    "Retrying in %.1fs...",
                    attempt, self.config.max_retries, exc, delay,
                )
                print(
                    f"  [retry] Connection error, attempt {attempt}/{self.config.max_retries}. "
                    f"Waiting {delay:.0f}s..."
                )
                time.sleep(delay)

        raise RuntimeError(
            f"API call failed after {self.config.max_retries} retries"
        ) from last_error

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
                # Return a partial result so reporting knows this probe existed
                result = ProbeResult(
                    probe_id=probe["id"],
                    domain=probe["domain"],
                    risk_tier=probe["risk_tier"],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    model=self.config.target_model,
                )
                result.stage1 = {"prompt": probe.get("stage1_prompt", ""), "response": "", "error": str(exc)}
                results.append(result)
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
