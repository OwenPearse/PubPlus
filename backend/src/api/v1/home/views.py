from __future__ import annotations

from django.http import JsonResponse

from apps.discovery.http import map_discovery_error
from common.auth.guards import optional_consumer_auth
from common.auth.request_context import get_auth_context
from services.discovery import DiscoveryFilterError
from services.home_feed.service import HomeFeedQuery, home_feed_to_dict, run_home_feed

# Per-section venue cap (three discovery passes). Conservative for Railway/TestFlight reliability; search keeps higher limits.
HOME_FEED_DEFAULT_LIMIT = 3
HOME_FEED_MAX_LIMIT = 6


def _optional_float(request, key: str) -> float | None:
    raw = request.GET.get(key)
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise DiscoveryFilterError("invalid_number", f"{key} must be numeric.") from exc


def _optional_home_limit(request, key: str) -> int:
    raw = request.GET.get(key)
    if raw is None or raw == "":
        return HOME_FEED_DEFAULT_LIMIT
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise DiscoveryFilterError("invalid_integer", f"{key} must be an integer.") from exc
    if value < 1 or value > HOME_FEED_MAX_LIMIT:
        raise DiscoveryFilterError(
            "invalid_limit",
            f"{key} must be between 1 and {HOME_FEED_MAX_LIMIT} for the home feed.",
        )
    return value


@optional_consumer_auth
def home_feed(request):
    try:
        allowed = {"lat", "lng", "suburb", "radius_m", "limit"}
        unsupported = sorted(set(request.GET.keys()) - allowed)
        if unsupported:
            raise DiscoveryFilterError(
                "unsupported_param",
                f"Unsupported query parameter(s): {', '.join(unsupported)}.",
            )
        query = HomeFeedQuery(
            lat=_optional_float(request, "lat"),
            lng=_optional_float(request, "lng"),
            suburb=request.GET.get("suburb"),
            radius_m=float(request.GET.get("radius_m", 5000.0)),
            limit=_optional_home_limit(request, "limit"),
        )
        auth_context = get_auth_context(request)
        result = run_home_feed(query, auth=auth_context)
    except Exception as exc:  # noqa: BLE001
        return map_discovery_error(exc)

    return JsonResponse(
        {
            "data": home_feed_to_dict(result),
            "meta": {
                "sections": [s.id for s in result.sections],
            },
        }
    )
