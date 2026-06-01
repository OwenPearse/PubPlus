"""CSV header mapping and row parsing for founder venue lead import."""

from __future__ import annotations

import csv
import io
from typing import Any

# canonical_field -> accepted header names (lowercase, normalized)
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "name": (
        "name",
        "venue_name",
        "business_name",
        "business",
        "company",
        "trading_name",
    ),
    "category": ("category", "type", "business_type", "venue_type", "industry"),
    "address_line": (
        "address",
        "street",
        "street_address",
        "address_line",
        "business_address",
    ),
    "suburb": ("suburb", "city", "town", "locality"),
    "state": ("state", "region"),
    "postcode": ("postcode", "postal_code", "zip"),
    "phone": ("phone", "business_phone", "telephone", "contact_phone"),
    "website": ("website", "business_website", "url", "site"),
    "email": ("email", "business_email", "contact_email"),
    "instagram_url": ("instagram", "instagram_url"),
    "facebook_url": ("facebook", "facebook_url"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lng", "lon"),
    "contact_name": ("contact_name", "manager_name", "owner_name"),
    "contact_role": ("contact_role", "role"),
}

IMPORTABLE_FIELDS = frozenset(FIELD_ALIASES.keys())


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_").replace("-", "_")


def build_header_map(headers: list[str]) -> dict[str, str]:
    """
    Map normalized CSV header -> canonical field name.
    First matching alias wins per canonical field.
    """
    normalized_headers = {_normalize_header(h): h for h in headers if h and h.strip()}
    canonical_by_header: dict[str, str] = {}
    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized_headers:
                original = normalized_headers[alias]
                canonical_by_header[original] = canonical
                break
    return canonical_by_header


def _cell_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def parse_csv_rows(csv_text: str) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Parse CSV text into (original_headers, list of raw row dicts keyed by original header).
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        return [], []
    headers = list(reader.fieldnames)
    rows: list[dict[str, Any]] = []
    for row in reader:
        rows.append(dict(row))
    return headers, rows


def map_row_to_lead_fields(
    row: dict[str, Any], header_map: dict[str, str]
) -> dict[str, str | None]:
    """Extract canonical lead fields from a CSV row."""
    out: dict[str, str | None] = {field: None for field in IMPORTABLE_FIELDS}
    for original_header, canonical in header_map.items():
        if canonical not in IMPORTABLE_FIELDS:
            continue
        raw = row.get(original_header)
        value = _cell_str(raw)
        if value is not None:
            out[canonical] = value
    return out
