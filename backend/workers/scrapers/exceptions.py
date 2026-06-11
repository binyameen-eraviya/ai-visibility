"""Scraper failure taxonomy.

Every adapter failure should carry enough context to debug without re-running:
which platform, and an excerpt of the page when the layout was unexpected. The
worker/runner layer maps these to a FAILED scrape_run with a clear message and,
later, retry/rotation decisions.
"""


class ScraperError(Exception):
    """Base class for all adapter failures."""

    def __init__(self, message: str, *, platform: str = None, page_excerpt: str = None):
        self.platform = platform
        self.page_excerpt = page_excerpt
        prefix = f"[{platform}] " if platform else ""
        super().__init__(f"{prefix}{message}")


class ScraperTimeout(ScraperError):
    """The answer never finished rendering within the allotted time."""


class CaptchaDetected(ScraperError):
    """The platform served a CAPTCHA / bot challenge."""


class RateLimited(ScraperError):
    """The platform returned a rate-limit / too-many-requests page."""


class UnexpectedLayout(ScraperError):
    """Expected elements (input, answer container) were not found."""
