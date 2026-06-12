import uuid
from datetime import date
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.daily_metric import DailyMetric as DailyMetricDB
from backend.interactors.helpers.project_access import verify_project_access

_GROUP_KEYS = {"date", "platform", "brand"}


def _weighted(rows, attr, weight="mention_count"):
    """mention/run-weighted average of an optional metric, or None."""
    pairs = [(getattr(r, attr), getattr(r, weight)) for r in rows
             if getattr(r, attr) is not None and getattr(r, weight)]
    total_w = sum(w for _, w in pairs)
    return (sum(v * w for v, w in pairs) / total_w) if total_w else None


def _aggregate(rows, key_field, key_value) -> dict:
    total_runs = sum(r.total_runs for r in rows)
    mention_count = sum(r.mention_count for r in rows)
    sov_w = sum(r.share_of_voice * r.total_runs for r in rows)
    web_w = sum(r.web_search_pct * r.total_runs for r in rows)
    point = {
        "visibility_pct": (mention_count / total_runs) if total_runs else 0.0,
        "avg_position": _weighted(rows, "avg_position"),
        "avg_sentiment": _weighted(rows, "avg_sentiment"),
        "share_of_voice": (sov_w / total_runs) if total_runs else 0.0,
        "total_runs": total_runs,
        "mention_count": mention_count,
        "web_search_pct": (web_w / total_runs) if total_runs else 0.0,
    }
    point[key_field] = key_value
    return point


async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    start_date: date,
    end_date: date,
    current_user,
    brand_id: uuid.UUID = None,
    platform_id: uuid.UUID = None,
    country_id: uuid.UUID = None,
    group_by: str = None,
):
    await verify_project_access(db, project_id, current_user)

    if group_by is not None and group_by not in _GROUP_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"group_by must be one of {sorted(_GROUP_KEYS)}",
        )

    try:
        metrics = await DailyMetricDB.get_report(
            db,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            brand_id=brand_id,
            platform_id=platform_id,
            country_id=country_id,
        )
        if not group_by:
            return metrics

        key_field = {"date": "date", "platform": "platform_id", "brand": "brand_id"}[group_by]
        buckets = defaultdict(list)
        for m in metrics:
            buckets[getattr(m, key_field)].append(m)
        points = [_aggregate(rows, key_field, key) for key, rows in buckets.items()]
        # Stable order: by date asc, else by visibility desc.
        if group_by == "date":
            points.sort(key=lambda p: p["date"])
        else:
            points.sort(key=lambda p: p["visibility_pct"], reverse=True)
        return points
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
