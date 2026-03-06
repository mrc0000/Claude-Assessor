"""Shared retry utility with exponential backoff for Anthropic API calls."""

import logging
import time

from config import Config

logger = logging.getLogger(__name__)


def api_call_with_retry(client, config: Config, label: str = "API", **kwargs):
    """Make an Anthropic API call with exponential backoff retry.

    Handles RateLimitError (429), overloaded (529), and connection errors.

    Args:
        client: anthropic.Anthropic instance.
        config: Config with max_retries, retry_base_delay, retry_on_overload, api_timeout.
        label: Human-readable label for log messages (e.g. "Probe", "Classifier").
        **kwargs: Passed directly to client.messages.create().

    Returns:
        The API response (anthropic.types.Message).
    """
    import anthropic

    last_error: Exception | None = None
    for attempt in range(1, config.max_retries + 1):
        try:
            return client.messages.create(timeout=config.api_timeout, **kwargs)
        except anthropic.RateLimitError as exc:
            last_error = exc
            delay = config.retry_base_delay * (2 ** (attempt - 1))
            logger.warning(
                "%s rate limited (429), attempt %d/%d. Retrying in %.1fs...",
                label, attempt, config.max_retries, delay,
            )
            print(
                f"  [retry] {label} rate limited, attempt {attempt}/{config.max_retries}. "
                f"Waiting {delay:.0f}s..."
            )
            time.sleep(delay)
        except anthropic.APIStatusError as exc:
            if exc.status_code == 529 and config.retry_on_overload:
                last_error = exc
                delay = config.retry_base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "%s API overloaded (529), attempt %d/%d. Retrying in %.1fs...",
                    label, attempt, config.max_retries, delay,
                )
                print(
                    f"  [retry] {label} overloaded, attempt {attempt}/{config.max_retries}. "
                    f"Waiting {delay:.0f}s..."
                )
                time.sleep(delay)
            else:
                raise
        except anthropic.APIConnectionError as exc:
            last_error = exc
            delay = config.retry_base_delay * (2 ** (attempt - 1))
            logger.warning(
                "%s connection error, attempt %d/%d. Retrying in %.1fs...",
                label, attempt, config.max_retries, delay,
            )
            print(
                f"  [retry] {label} connection error, attempt {attempt}/{config.max_retries}. "
                f"Waiting {delay:.0f}s..."
            )
            time.sleep(delay)

    raise RuntimeError(
        f"{label} call failed after {config.max_retries} retries"
    ) from last_error
