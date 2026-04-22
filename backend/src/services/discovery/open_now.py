"""
Centralized open-now: published `venue_hours_regular` + `venue_hours_exception`
+ optional `venue_hours_uncertainty` (strength, not a substitute for hours).

See `common.time.venue_local` for the explicit IANA country → timezone map.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from apps.venues.services.published_venue_read import (
    PublishedExceptionHoursRow,
    PublishedRegularHoursRow,
    PublishedVenueReadBundle,
)
from common.time.venue_local import local_now_for_venue


def schema_dow(d: date) -> int:
    """0=Sunday .. 6=Saturday (`venue_hours_regular.day_of_week`)."""
    return (d.weekday() + 1) % 7


def _parse_hhmm(value: str | None) -> time | None:
    if value is None or value == "":
        return None
    h, m, *_ = value.split(":", 2)
    return time(int(h), int(m))


def _in_range(today: date, e: PublishedExceptionHoursRow) -> bool:
    s = e.start_date
    z = e.end_date
    return s <= today.isoformat() <= z


def _span_days(e: PublishedExceptionHoursRow) -> int:
    a = date.fromisoformat(e.start_date)
    b = date.fromisoformat(e.end_date)
    return (b - a).days


def _exception_sort_key(
    e: PublishedExceptionHoursRow, today: date
) -> tuple[int, int, str]:
    if e.exception_kind == "closed_all_day":
        p = 0
    elif e.exception_kind == "open_by_appointment_or_special":
        p = 1
    else:
        p = 2
    return (p, _span_days(e), e.start_date)


def _pick_today_exception(
    ex: list[PublishedExceptionHoursRow], today: date
) -> PublishedExceptionHoursRow | None:
    c = [e for e in ex if _in_range(today, e)]
    if not c:
        return None
    return sorted(c, key=lambda e: _exception_sort_key(e, today))[0]


def _build_row_segment(
    r: PublishedRegularHoursRow, d: date, zone: ZoneInfo
) -> tuple[datetime, datetime] | None:
    oa = _parse_hhmm(r.opens_at)
    ca = _parse_hhmm(r.closes_at)
    if oa is None or ca is None:
        return None
    if r.crosses_midnight:
        a = datetime.combine(d, oa, tzinfo=zone)
        b = datetime.combine(d + timedelta(days=1), ca, tzinfo=zone)
    else:
        a = datetime.combine(d, oa, tzinfo=zone)
        b = datetime.combine(d, ca, tzinfo=zone)
    if b <= a:
        return None
    return a, b


def _build_regular_segs(
    reg: list[PublishedRegularHoursRow], y: date, t: date, zone: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    d_y, d_t = schema_dow(y), schema_dow(t)
    out: list[tuple[datetime, datetime]] = []
    for r in reg:
        if r.day_of_week == d_t:
            seg = _build_row_segment(r, t, zone)
            if seg:
                out.append(seg)
        if r.day_of_week == d_y:
            if r.crosses_midnight:
                seg = _build_row_segment(r, y, zone)
                if seg:
                    out.append(seg)
    return out


def _segments_from_modified(
    e: PublishedExceptionHoursRow, d: date, zone: ZoneInfo
) -> list[tuple[datetime, datetime]]:
    oa = _parse_hhmm(e.opens_at)
    ca = _parse_hhmm(e.closes_at)
    if oa is None or ca is None:
        return []
    if e.crosses_midnight:
        a = datetime.combine(d, oa, tzinfo=zone)
        b = datetime.combine(d + timedelta(days=1), ca, tzinfo=zone)
    else:
        a = datetime.combine(d, oa, tzinfo=zone)
        b = datetime.combine(d, ca, tzinfo=zone)
    if b <= a:
        return []
    return [(a, b)]


def _in_any(t: datetime, segs: list[tuple[datetime, datetime]]) -> bool:
    for a, b in segs:
        if a <= t < b:
            return True
    return False


class OpenNowInternalState(str, Enum):
    DETERMINABLE_OPEN = "determinable_open"
    DETERMINABLE_CLOSED = "determinable_closed"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class OpenNowResult:
    internal: OpenNowInternalState
    public_open_now: bool | None
    public_open_now_uncomputed: bool


def compute_open_now(
    bundle: PublishedVenueReadBundle,
    *,
    hours_uncertainty_level: str | None = None,
    at_utc: datetime | None = None,
) -> OpenNowResult:
    zone, local = local_now_for_venue(
        bundle.core.country_code, at_utc=at_utc
    )
    u = hours_uncertainty_level
    ex = list(bundle.hours_exceptions)
    reg = list(bundle.hours_regular)
    today = local.date()
    yday = today - timedelta(days=1)

    tod = _pick_today_exception(ex, today)
    if tod and tod.exception_kind == "closed_all_day":
        return OpenNowResult(
            OpenNowInternalState.DETERMINABLE_CLOSED, False, False
        )
    if tod and tod.exception_kind == "open_by_appointment_or_special":
        return OpenNowResult(
            OpenNowInternalState.INDETERMINATE, None, True
        )

    segs: list[tuple[datetime, datetime]] = []
    if tod and tod.exception_kind == "modified_hours":
        segs = _segments_from_modified(tod, today, zone)
    else:
        segs = _build_regular_segs(reg, yday, today, zone)

    has_published_baseline = bool(reg) or bool(
        tod and tod.exception_kind == "modified_hours"
    )
    is_open = _in_any(local, segs) if segs else False
    if not segs and not has_published_baseline:
        return OpenNowResult(
            OpenNowInternalState.INDETERMINATE, None, True
        )

    if is_open:
        if u in (None, "resolved_confident"):
            return OpenNowResult(
                OpenNowInternalState.DETERMINABLE_OPEN, True, False
            )
        if u == "partial":
            return OpenNowResult(
                OpenNowInternalState.INDETERMINATE, None, True
            )
        return OpenNowResult(
            OpenNowInternalState.INDETERMINATE, None, True
        )
    if u in (None, "resolved_confident", "partial"):
        return OpenNowResult(
            OpenNowInternalState.DETERMINABLE_CLOSED, False, False
        )
    return OpenNowResult(
        OpenNowInternalState.INDETERMINATE, None, True
    )
