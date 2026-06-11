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
    OTHER = "OTHER"
