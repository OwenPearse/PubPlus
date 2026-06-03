"""
Local clock for venue open-now evaluation (IANA timezones, zoneinfo).

Strategy (explicit, documented):
- `country_code == "AU"` → `Australia/Sydney` (MVP: single default for AU)
- all other `country_code` values → `UTC` until region-level timezone
  is published; this avoids false precision without DB-backed zones.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

VENUE_TIMEZONE_STRATEGY = "country_default_au_sydney_else_utc"

_AU = ZoneInfo("Australia/Sydney")
_UTC = ZoneInfo("UTC")


def resolve_venue_timezone(country_code: str) -> ZoneInfo:
    c = (country_code or "AU").upper()
    if c == "AU":
        return _AU
    return _UTC


def local_now_for_venue(
    country_code: str, *, at_utc: datetime | None = None
) -> tuple[ZoneInfo, datetime]:
    """
    Return (zone, now_local) where `now_local` is wall-clock in `zone`
    (aware). If at_utc is given it must be timezone-aware UTC.
    """
    zone = resolve_venue_timezone(country_code)
    base = at_utc or datetime.now(ZoneInfo("UTC"))
    if base.tzinfo is None:
        base = base.replace(tzinfo=ZoneInfo("UTC"))
    return zone, base.astimezone(zone)
