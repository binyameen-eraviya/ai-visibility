from enum import Enum

class UserRole(Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class AdapterType(Enum):
    SCRAPER = "SCRAPER"
    API = "API"

class PromptStatus(Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

class TrackingFrequency(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"

class ScrapeStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

class ScrapeAccountStatus(Enum):
    ACTIVE = "ACTIVE"
    COOLDOWN = "COOLDOWN"
    BANNED = "BANNED"
    DISABLED = "DISABLED"

class SourceType(Enum):
    REVIEW_SITE = "REVIEW_SITE"
    REDDIT = "REDDIT"
    EDITORIAL = "EDITORIAL"
    CORPORATE = "CORPORATE"
    UGC = "UGC"
    REFERENCE = "REFERENCE"
    INSTITUTIONAL = "INSTITUTIONAL"  # .gov / .edu / NGOs / standards bodies
    COMPETITOR = "COMPETITOR"  # domain belongs to a tracked competitor brand
    OTHER = "OTHER"


class UrlType(Enum):
    """What kind of page a cited URL is (from path/title heuristics or LLM)."""
    LISTICLE = "LISTICLE"
    ARTICLE = "ARTICLE"
    HOMEPAGE = "HOMEPAGE"
    PRODUCT_PAGE = "PRODUCT_PAGE"
    COMPARISON = "COMPARISON"
    HOW_TO = "HOW_TO"
    DISCUSSION = "DISCUSSION"
    OTHER = "OTHER"


class DomainClassifier(Enum):
    """How a domain_classifications row was produced (provenance for the cache)."""
    KNOWN_LIST = "KNOWN_LIST"
    LLM = "LLM"
    BRAND_MATCH = "BRAND_MATCH"
    MANUAL = "MANUAL"
