import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import ScrapeStatus
from backend.utils.schema.request import ScrapeRunRequest
from backend.database.models.prompt import Prompt as PromptDB
from backend.database.models.platform import Platform as PlatformDB
from backend.database.models.country import Country as CountryDB
from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB
from backend.database.models.tracking_config import TrackingConfig as TrackingConfigDB
from backend.interactors.helpers.project_access import verify_project_access
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

        # Milestone 4: create the run as PENDING and hand it to Celery. The
        # endpoint returns immediately (<1s); the worker drives the scrape and
        # chains parse -> aggregate. The frontend polls GET /runs/{id}.
        run = await ScrapeRunDB.create(
            db, tracking_config_id=tracking_config.id, status=ScrapeStatus.PENDING
        )

        # Import here so the API process doesn't pull in the worker task graph at
        # module load, and so tests can monkeypatch the enqueue cleanly.
        from backend.workers.tasks.scrape_task import run_scrape_task
        run_scrape_task.delay(
            tracking_config_id=str(tracking_config.id),
            scrape_run_id=str(run.id),
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
