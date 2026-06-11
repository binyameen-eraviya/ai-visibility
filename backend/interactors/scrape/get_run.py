import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.schema.response import ScrapeRunDetailResponse
from backend.database.models.scrape_run import ScrapeRun as ScrapeRunDB
from backend.services.storage import LocalStorageService
from backend.interactors.helpers.project_access import verify_project_access
from backend.utils.custom_exceptions import NotFound as DataNotFoundException


async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    run_id: uuid.UUID,
    current_user,
):
    await verify_project_access(db, project_id, current_user)

    try:
        run = await ScrapeRunDB.find_by_id_and_project(db, run_id, project_id)

        detail = ScrapeRunDetailResponse.model_validate(run)

        # Attach the stored answer if this run produced one. A missing/unreadable
        # file is non-fatal -- the metadata is still useful.
        if run.raw_storage_path:
            try:
                detail.raw = await LocalStorageService().get_raw(run.raw_storage_path)
            except Exception:
                detail.raw = None
        return detail
    except DataNotFoundException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrape run not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
