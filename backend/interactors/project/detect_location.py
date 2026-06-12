"""Best-effort IP -> country detection for onboarding pre-fill.

No GeoIP database is bundled, so this does a best-effort lookup against a free
no-key IP API for public client IPs and degrades to nulls otherwise (private /
loopback IPs in local Docker, lookup failure, timeout). The frontend treats this
as a hint and falls back to the browser locale, so nulls are fine.
"""

import logging
import ipaddress

import httpx

logger = logging.getLogger(__name__)

_LOOKUP_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode"


def _client_ip(request) -> str:
    # Honor the first hop of X-Forwarded-For when behind a proxy, else peer IP.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


def _is_public(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


async def call(request, current_user) -> dict:
    ip = _client_ip(request)
    result = {"ip": ip or None, "country_code": None, "country_name": None}

    if not ip or not _is_public(ip):
        return result  # private/loopback (e.g. local Docker) -> no geo

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(_LOOKUP_URL.format(ip=ip))
        data = resp.json() if resp.status_code == 200 else {}
        if data.get("status") == "success":
            result["country_code"] = data.get("countryCode")
            result["country_name"] = data.get("country")
    except Exception as e:
        logger.info("detect_location: lookup failed for %s: %s", ip, type(e).__name__)

    return result
