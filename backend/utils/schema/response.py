from pydantic import BaseModel
import uuid
from datetime import datetime, date
from typing import List, Optional

from backend.utils.enums import (
    AdapterType,
    PromptStatus,
    ScrapeAccountStatus,
    ScrapeStatus,
    SourceType,
    TrackingFrequency,
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
    id: uuid.UUID
    project_id: uuid.UUID
    brand_id: uuid.UUID
    platform_id: uuid.UUID
    country_id: uuid.UUID
    date: date
    visibility_pct: float
    avg_position: Optional[float]
    avg_sentiment: Optional[float]
    share_of_voice: float
    total_runs: int
    mention_count: int

    class Config:
        from_attributes = True

class SourceMetricResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    domain: str
    source_type: SourceType
    date: date
    citation_count: int

    class Config:
        from_attributes = True

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
