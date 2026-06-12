from pydantic import BaseModel
import uuid
from datetime import datetime, date
from typing import List, Optional

# Alias so an Optional field literally named `date` doesn't shadow the `date`
# type during Pydantic's annotation resolution (class attr `date=None` would
# otherwise be picked up, collapsing the type to NoneType).
DateType = date

from backend.utils.enums import (
    AdapterType,
    PromptStatus,
    ScrapeAccountStatus,
    ScrapeStatus,
    SourceType,
    TrackingFrequency,
    UrlType,
)

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    verified_at: Optional[datetime]

    class Config:
        from_attributes = True

class CompetitorSuggestion(BaseModel):
    name: str
    reason: str = ""

class WebsiteAnalysisResponse(BaseModel):
    brand_name: str
    brand_aliases: List[str] = []
    industry: str = ""
    location: str = ""
    company_scale: str = ""
    competitors: List[CompetitorSuggestion] = []
    suggested_prompts: List[str] = []
    prompt_topics: List[str] = []

class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str

    class Config:
        from_attributes = True

class SignupResponse(BaseModel):
    message: str
    user: UserResponse
    organization_id: uuid.UUID
    email_sent: bool
    verification_required: bool
    next_step: str

    class Config:
        from_attributes = True

class VerificationResponse(BaseModel):
    message: str
    user: UserResponse
    verified_at: datetime
    next_step: str

    class Config:
        from_attributes = True

class PasswordResetResponse(BaseModel):
    message: str
    email_sent: bool
    next_step: str

    class Config:
        from_attributes = True

class PasswordResetCompleteResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    next_step: str

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    website_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class BrandResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    aliases: List[str]
    is_primary: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TopicResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class TagResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class PromptResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    text: str
    status: PromptStatus
    topic: Optional[TopicResponse]
    tags: List[TagResponse]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TrackingConfigResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    prompt_id: uuid.UUID
    platform_id: uuid.UUID
    country_id: uuid.UUID
    frequency: TrackingFrequency
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PlatformResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    adapter_type: AdapterType
    is_active: bool

    class Config:
        from_attributes = True

class CountryResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True

class DailyMetricResponse(BaseModel):
    # Key fields are optional so grouped responses (group_by=date/platform/brand)
    # can omit the dimensions they collapse over.
    id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    platform_id: Optional[uuid.UUID] = None
    country_id: Optional[uuid.UUID] = None
    date: Optional[DateType] = None
    visibility_pct: float
    avg_position: Optional[float] = None
    avg_sentiment: Optional[float] = None
    share_of_voice: float
    total_runs: int
    mention_count: int
    web_search_pct: float = 0.0

    class Config:
        from_attributes = True

class SourceMetricResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    domain: str
    source_type: SourceType
    url_type: UrlType = UrlType.OTHER
    date: Optional[DateType] = None
    citation_count: int
    retrieved_pct: float = 0.0
    citation_rate: float = 0.0

    class Config:
        from_attributes = True

class QueueStatusResponse(BaseModel):
    workers: int
    worker_names: List[str] = []
    active_tasks: int
    reserved_tasks: int
    scheduled_tasks: int
    queues: dict = {}

class GapAnalysisResponse(BaseModel):
    domain: str
    domain_type: SourceType = SourceType.OTHER
    gap_score: int
    competitor_mentions: int
    retrieved_pct: float = 0.0

class BrandPlatformInsight(BaseModel):
    platform_id: uuid.UUID
    platform_name: str
    visibility_pct: float
    avg_sentiment: Optional[float] = None
    avg_position: Optional[float] = None
    share_of_voice: float

class BrandInsightResponse(BaseModel):
    brand_id: uuid.UUID
    brand_name: str
    is_primary: bool = False
    platforms: List[BrandPlatformInsight] = []

class ScrapeRunResponse(BaseModel):
    id: uuid.UUID
    tracking_config_id: uuid.UUID
    status: ScrapeStatus
    raw_storage_path: Optional[str]
    screenshot_path: Optional[str]
    error: Optional[str]
    account_id: Optional[uuid.UUID]
    duration_ms: Optional[int]
    scraped_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class ScrapeRunDetailResponse(ScrapeRunResponse):
    # The raw captured answer read back from storage (None if the run failed or
    # the file is missing).
    raw: Optional[dict] = None

class ScrapeAccountResponse(BaseModel):
    id: uuid.UUID
    platform_id: uuid.UUID
    email: str
    daily_quota_used: int
    daily_quota_limit: int
    cooldown_until: Optional[datetime]
    status: ScrapeAccountStatus
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
