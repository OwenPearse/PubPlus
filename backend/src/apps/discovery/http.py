from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse

from common.auth.context import AuthContext
from services.discovery import (
    DiscoveryError,
    DiscoveryFilterError,
    DiscoveryMode,
    DiscoveryMvpFilters,
    DiscoveryQueryError,
)
from services.discovery.q_text import normalize_discovery_q


COMMON_DISCOVERY_QUERY_PARAMS = frozenset(
    {
        "suburb",
        "lat",
        "lng",
        "radius_m",
        "north",
        "south",
        "east",
        "west",
        "open_now",
        "meal_specials",
        "drink_types",
        "venue_features",
        "events",
        "q",
        "limit",
    }
)


def error_response(*, code: str, message: str, status: int = 400) -> JsonResponse:
    return JsonResponse(
        {"error": {"code": code, "message": message}},
        status=status,
    )


def map_discovery_error(err: Exception) -> JsonResponse:
    if isinstance(err, (DiscoveryFilterError, DiscoveryQueryError)):
        return error_response(code=err.code, message=err.message, status=400)
    if isinstance(err, DiscoveryError):
        return error_response(
            code="discovery_error",
            message="Discovery query could not be completed.",
            status=400,
        )
    return error_response(
        code="internal_error",
        message="Unexpected error while processing discovery request.",
        status=500,
    )


def _parse_bool(value: str, *, key: str) -> bool:
    v = value.strip().lower()
    if v in {"true", "1"}:
        return True
    if v in {"false", "0"}:
        return False
    raise DiscoveryFilterError(
        "invalid_boolean",
        f"{key} must be a boolean (true/false).",
    )


def _parse_float(raw: str, *, key: str) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise DiscoveryFilterError("invalid_number", f"{key} must be numeric.") from exc


def _parse_int(raw: str, *, key: str) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise DiscoveryFilterError("invalid_integer", f"{key} must be an integer.") from exc


def _get_optional_float(request: HttpRequest, key: str) -> float | None:
    raw = request.GET.get(key)
    if raw is None or raw == "":
        return None
    return _parse_float(raw, key=key)


def _get_optional_int(request: HttpRequest, key: str, *, default: int) -> int:
    raw = request.GET.get(key)
    if raw is None or raw == "":
        return default
    return _parse_int(raw, key=key)


def _get_optional_bool(request: HttpRequest, key: str) -> bool | None:
    raw = request.GET.get(key)
    if raw is None or raw == "":
        return None
    return _parse_bool(raw, key=key)


def _parse_list_param(request: HttpRequest, key: str) -> list[str]:
    values = request.GET.getlist(key)
    parsed: list[str] = []
    for value in values:
        for item in value.split(","):
            item0 = item.strip()
            if item0:
                parsed.append(item0)
    return parsed


def parse_discovery_filters_from_request(
    request: HttpRequest, *, mode: DiscoveryMode
) -> DiscoveryMvpFilters:
    unsupported = sorted(set(request.GET.keys()) - COMMON_DISCOVERY_QUERY_PARAMS)
    if unsupported:
        raise DiscoveryFilterError(
            "unsupported_param",
            f"Unsupported query parameter(s): {', '.join(unsupported)}.",
        )

    return DiscoveryMvpFilters(
        suburb=request.GET.get("suburb"),
        lat=_get_optional_float(request, "lat"),
        lng=_get_optional_float(request, "lng"),
        radius_m=_get_optional_float(request, "radius_m"),
        north=_get_optional_float(request, "north"),
        south=_get_optional_float(request, "south"),
        east=_get_optional_float(request, "east"),
        west=_get_optional_float(request, "west"),
        open_now=_get_optional_bool(request, "open_now"),
        meal_specials=_parse_list_param(request, "meal_specials"),
        drink_types=_parse_list_param(request, "drink_types"),
        venue_features=_parse_list_param(request, "venue_features"),
        require_published_events=bool(
            _get_optional_bool(request, "events") is True
        ),
        q=normalize_discovery_q(request.GET.get("q")),
        limit=_get_optional_int(request, "limit", default=50),
    )


def apply_optional_save_enrichment(card: Any, *, auth: AuthContext | None) -> Any:
    if auth is None:
        return card

    from apps.venues.services.save_enrichment import apply_save_to_card

    return apply_save_to_card(card, auth=auth, venue_id=card.id)
