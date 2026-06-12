import uuid
from datetime import date
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.utils.enums import SourceType
from backend.database.models.gap_score import GapScore as GapScoreDB
from backend.database.models.source_metric import SourceMetric as SourceMetricDB
from backend.interactors.helpers.project_access import verify_project_access


async def call(
    db: AsyncSession,
    project_id: uuid.UUID,
    start_date: date,
    end_date: date,
    current_user,
    min_competitors: int = 0,
):
    """Domains ranked by content-gap score over a date range.

    Gap scores and source metrics are both keyed by (project, domain, date);
    we sum gap/competitor counts across the range per domain and decorate each
    with its domain type + retrieved_pct from source_metrics.
    """
    await verify_project_access(db, project_id, current_user)

    try:
        gap_rows = await GapScoreDB.get_report(db, project_id, start_date, end_date, min_competitors=0)
        source_rows = await SourceMetricDB.get_report(db, project_id, start_date, end_date)

        # domain -> (source_type, mean retrieved_pct) from source_metrics.
        stype_by_domain = {}
        retr_by_domain = defaultdict(list)
        for s in source_rows:
            stype_by_domain.setdefault(s.domain, s.source_type)
            retr_by_domain[s.domain].append(s.retrieved_pct)

        agg = defaultdict(lambda: {"gap": 0, "comp": 0})
        for g in gap_rows:
            agg[g.domain]["gap"] += g.gap_score
            agg[g.domain]["comp"] += g.competitor_mentions

        results = []
        for domain, a in agg.items():
            if a["comp"] < min_competitors:
                continue
            retr = retr_by_domain.get(domain) or [0.0]
            results.append({
                "domain": domain,
                "domain_type": stype_by_domain.get(domain, SourceType.OTHER),
                "gap_score": a["gap"],
                "competitor_mentions": a["comp"],
                "retrieved_pct": sum(retr) / len(retr),
            })
        results.sort(key=lambda r: r["gap_score"], reverse=True)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
