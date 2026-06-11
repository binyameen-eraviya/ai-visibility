"""Adapter registry: platform name -> adapter class.

The run-now service and the future Celery task resolve adapters through here, so
adding a platform in Milestone 5 is a one-line registration -- no endpoint or
runner changes.
"""

from backend.workers.scrapers.base_adapter import BasePlatformAdapter
from backend.workers.scrapers.perplexity import PerplexityAdapter

ADAPTER_REGISTRY = {
    "perplexity": PerplexityAdapter,
    # "chatgpt": ChatGPTAdapter,        # Milestone 5
    # "gemini": GeminiAdapter,          # Milestone 5
    # "ai_overview": AIOverviewAdapter, # Milestone 5
    # "copilot": CopilotAdapter,        # Milestone 5
}


def get_adapter(platform_name: str) -> BasePlatformAdapter:
    """Instantiate the adapter registered for a platform name.

    Raises ValueError if no adapter is registered (e.g. a seeded platform whose
    adapter ships in a later milestone).
    """
    adapter_cls = ADAPTER_REGISTRY.get(platform_name)
    if adapter_cls is None:
        raise ValueError(f"No scraper adapter registered for platform '{platform_name}'")
    return adapter_cls()
