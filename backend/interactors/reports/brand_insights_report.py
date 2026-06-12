import uuid
from datetime import date
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.daily_metric import DailyMetric as DailyMetricDB
from backend.database.models.brand import Brand as BrandDB
from backend.database.models.platform import Platform as PlatformDB
from backend.interactors.helpers.project_access import verify_project_access


def _weighted(rows, attr, weight="mention_count"):
    pairs = [(getattr(r, attr), getattr(r, weight)) for r in rows
             if getattr(r, attr) is not None and getattr(r, weight)]
    total_w = sum(w for _, w in pairs)
    return (sum(v * w for v, w in pairs) / total_w) if total_w else None


async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    start_date: date,
    end_date: date,
    current_user,
):
    """Per-brand metrics broken down by platform (the performance matrix)."""
    await verify_project_access(db, project_id, current_user)

    try:
        metrics = await DailyMetricDB.get_report(db, project_id, start_date, end_date)
        brands = await BrandDB.find_by_project(db, project_id)
        platforms = await PlatformDB.get_list(db)
        platform_name = {p.id: p.display_name for p in platforms}

        # (brand_id, platform_id) -> rows
        buckets = defaultdict(list)
        for m in metrics:
            buckets[(m.brand_id, m.platform_id)].append(m)

        results = []
        for brand in brands:
            platform_points = []
            for platform in platforms:
                rows = buckets.get((brand.id, platform.id))
                if not rows:
                    continue
                total_runs = sum(r.total_runs for r in rows)
                mention_count = sum(r.mention_count for r in rows)
                sov_w = sum(r.share_of_voice * r.total_runs for r in rows)
                platform_points.append({
                    "platform_id": platform.id,
                    "platform_name": platform_name.get(platform.id, platform.name),
                    "visibility_pct": (mention_count / total_runs) if total_runs else 0.0,
                    "avg_sentiment": _weighted(rows, "avg_sentiment"),
                    "avg_position": _weighted(rows, "avg_position"),
                    "share_of_voice": (sov_w / total_runs) if total_runs else 0.0,
                })
            results.append({
                "brand_id": brand.id,
                "brand_name": brand.name,
                "is_primary": brand.is_primary,
                "platforms": platform_points,
            })
        # Primary brand first, then brands with the most platform coverage.
        results.sort(key=lambda b: (not b["is_primary"], -len(b["platforms"])))
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
