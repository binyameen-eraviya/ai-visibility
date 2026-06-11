"""BasePlatformAdapter: the uniform interface every platform adapter implements.

Hard architectural requirement: workers call this interface only. Whether an
adapter drives Playwright or calls an official API is an internal detail.
Concrete adapters arrive in Milestone 2 (Perplexity first) and Milestone 5.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RawAnswer:
    """Uniform result of running one prompt on one platform."""

    answer_text: str
    sources: list = field(default_factory=list)  # cited URLs, in order
    raw_html: str = None
    screenshot: bytes = None
    metadata: dict = field(default_factory=dict)  # model name, timings, etc.


class BasePlatformAdapter(ABC):
    """Abstract adapter for one AI answer platform."""

    platform_name: str = None  # e.g. "perplexity"

    @abstractmethod
    async def run_prompt(self, prompt_text: str, account: dict, proxy: dict = None) -> RawAnswer:
        """Submit a prompt and return the captured answer.

        Args:
            prompt_text: The prompt to ask the platform.
            account: Checked-out account from the account pool (credentials/cookies).
            proxy: Optional proxy from the proxy pool, matched to target country.

        Returns:
            RawAnswer with the full answer text, cited sources, and raw capture.

        Raises:
            Adapter-specific exceptions for login walls, CAPTCHAs, rate limits;
            the worker layer handles retries/backoff.
        """
        raise NotImplementedError
