import uuid
from typing import List, Optional

from pydantic import BaseModel

from backend.utils.enums import PromptStatus, TrackingFrequency

class UserSignup(BaseModel):
    user_name: str
    email: str
    organization_name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class SignupVerify(BaseModel):
    email: str
    token: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordReset(BaseModel):
    email: str
    token: str
    new_password: str

class AnalyzeWebsiteRequest(BaseModel):
    url: str

class ProjectProfileFields(BaseModel):
    description: Optional[str] = None
    industry: Optional[str] = None
    brand_identity: Optional[List[str]] = None
    products_services: Optional[List[str]] = None
    detected_location: Optional[str] = None
    detected_language: Optional[str] = None
    detected_timezone: Optional[str] = None
    favicon_url: Optional[str] = None

class ProjectCreate(ProjectProfileFields):
    name: str
    website_url: Optional[str] = None

class ProjectUpdate(ProjectProfileFields):
    name: Optional[str] = None
    website_url: Optional[str] = None

class BrandCreate(BaseModel):
    name: str
    aliases: List[str] = []
    is_primary: bool = False
    website_url: Optional[str] = None
    favicon_url: Optional[str] = None

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    aliases: Optional[List[str]] = None
    is_primary: Optional[bool] = None
    website_url: Optional[str] = None
    favicon_url: Optional[str] = None

class PromptCreate(BaseModel):
    text: str
    topic_id: Optional[uuid.UUID] = None
    tag_ids: List[uuid.UUID] = []

class PromptUpdate(BaseModel):
    text: Optional[str] = None
    topic_id: Optional[uuid.UUID] = None
    status: Optional[PromptStatus] = None

class TrackingConfigCreate(BaseModel):
    prompt_id: uuid.UUID
    platform_id: uuid.UUID
    country_id: uuid.UUID
    frequency: TrackingFrequency = TrackingFrequency.DAILY

class TrackingConfigBulkCreate(BaseModel):
    configs: List[TrackingConfigCreate]

class TopicCreate(BaseModel):
    name: str

class TagCreate(BaseModel):
    name: str

class ScrapeRunRequest(BaseModel):
    platform_id: uuid.UUID
    # Optional for now -- ignored until proxies land (Milestone 4). When omitted,
    # the run defaults to the US country (or the first available country).
    country_id: Optional[uuid.UUID] = None

class ScrapeAccountCreate(BaseModel):
    platform_id: uuid.UUID
    email: str
    # Session cookies captured from a logged-in browser, so we don't re-login.
    cookies: dict = {}
    daily_quota_limit: int = 10
