import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.request import ScrapeRunRequest
from backend.database.models.prompt import Prompt as PromptDB
from backend.database.models.platform import Platform as PlatformDB
from backend.database.models.country import Country as CountryDB
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.interactors.helpers.project_access import verify_project_access
from backend.services.scrape_runner import run_scrape
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    prompt_id: uuid.UUID,
    payload: ScrapeRunRequest,
    current_user,
):
    await verify_project_access(db, project_id, current_user)

    try:
        prompt = await PromptDB.find_by_id(db, prompt_id)
        if prompt.project_id != project_id:
            raise DataNotFoundException("Prompt not found")

        platform = await PlatformDB.find_by_id(db, payload.platform_id)

        # country_id is optional for now; default to US (or first available).
        if payload.country_id:
            country = await CountryDB.find_by_id(db, payload.country_id)
        else:
            country = await CountryDB.find_default(db)

        # Look up or create the tracking config for this scope.
        tracking_config = await TrackingConfigDB.find_by_scope(
            db, prompt_id=prompt_id, platform_id=platform.id, country_id=country.id
        )
        if tracking_config is None:
            tracking_config = await TrackingConfigDB.create(
                db,
                project_id=project_id,
                prompt_id=prompt_id,
                platform_id=platform.id,
                country_id=country.id,
            )

        # Synchronous for Milestone 2 -- blocks 15-45s. Moves to Celery in M4.
        run = await run_scrape(
            db,
            project_id=project_id,
            platform_id=platform.id,
            platform_name=platform.name,
            tracking_config_id=tracking_config.id,
            prompt_text=prompt.text,
        )
        return run
    except DataNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
