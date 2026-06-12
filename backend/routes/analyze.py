from fastapi import APIRouter, Depends

from backend.service.auth_handler import AuthHandler
from backend.utils.schema.request import AnalyzeWebsiteRequest
from backend.utils.schema.response import WebsiteAnalysisResponse
from backend.interactors.project import analyze_website as analyze_website_interactor

router = APIRouter(prefix="/api", tags=["onboarding"])


@router.post("/analyze-website", response_model=WebsiteAnalysisResponse)
async def analyze_website(
    payload: AnalyzeWebsiteRequest,
    current_user=Depends(AuthHandler.get_current_user),
):
    return await analyze_website_interactor.call(payload, current_user)
