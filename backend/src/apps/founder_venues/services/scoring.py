"""
Deterministic founder-fit scoring for venue leads (Stage 3).

Pure functions only — no database access. Persistence in founder_fit_db.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from apps.founder_venues.services.contact_safety import (
    classify_email_contact_safety,
    is_high_confidence_business_email,
)

# Inner Melbourne / first-launch priority suburbs (normalized lowercase).
HIGH_PRIORITY_LAUNCH_SUBURBS: frozenset[str] = frozenset(
    {
        "melbourne",
        "melbourne cbd",
        "carlton",
        "fitzroy",
        "collingwood",
        "richmond",
        "south yarra",
        "prahran",
        "brunswick",
        "north melbourne",
        "southbank",
        "docklands",
        "st kilda",
        "abbotsford",
        "cremorne",
        "windsor",
        "south melbourne",
        "port melbourne",
        "footscray",
        "northcote",
        "thornbury",
        "hawthorn",
    }
)

REGIONAL_VIC_SUBURBS: frozenset[str] = frozenset(
    {
        "geelong",
        "ballarat",
        "bendigo",
        "shepparton",
        "wodonga",
        "mildura",
        "warrnambool",
        "traralgon",
    }
)

AU_STATE_CODES: frozenset[str] = frozenset(
    {"ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"}
)

STRONG_CATEGORY_TERMS: frozenset[str] = frozenset(
    {
        "pub",
        "bar",
        "hotel",
        "tavern",
        "brewery",
        "brewpub",
        "sports bar",
        "beer garden",
        "live music venue",
        "cocktail bar",
        "wine bar",
    }
)

LIKELY_HOSPITALITY_TERMS: frozenset[str] = frozenset(
    {
        "bistro",
        "gastropub",
        "lounge",
        "nightclub",
        "club",
        "inn",
        "ale house",
        "taproom",
        "saloon",
        "dining",
        "restaurant",
    }
)

CHAIN_NAME_MARKERS: frozenset[str] = frozenset(
    {
        "woolworths",
        "coles",
        "mcdonald",
        "kfc",
        "hungry jack",
        "starbucks",
        "dan murphy",
        "bws",
        "liquorland",
    }
)

PRODUCT_FIT_KEYWORDS: frozenset[str] = frozenset(
    {
        "trivia",
        "live music",
        "sports",
        "rooftop",
        "beer garden",
        "craft beer",
        "brewery",
        "functions",
        "events",
        "happy hour",
        "specials",
        "parma",
        "steak night",
        "comedy",
        "open mic",
    }
)

_UNSAFE_EMAIL_CLASSES = frozenset(
    {"likely_personal_or_unsafe", "personal_business_contact"}
)

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class FounderFitScoreResult:
    score: int
    breakdown: dict[str, Any]


def _norm_suburb(value: Any) -> str | None:
    if value is None:
        return None
    text = _WHITESPACE_RE.sub(" ", str(value).strip().lower())
    return text or None


def _norm_state(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if len(text) == 2 and text in AU_STATE_CODES:
        return text
    return text if text in AU_STATE_CODES else None


def _text_blob(lead: Mapping[str, Any]) -> str:
    parts = [
        lead.get("name"),
        lead.get("category"),
        lead.get("notes"),
        lead.get("source_summary"),
    ]
    return " ".join(str(p).lower() for p in parts if p)


def _score_location(
    lead: Mapping[str, Any],
    *,
    positive: list[str],
    negative: list[str],
) -> int:
    suburb = _norm_suburb(lead.get("suburb"))
    state = _norm_state(lead.get("state"))

    if not suburb and not state:
        negative.append("No suburb or state")
        return 0

    if suburb and suburb in HIGH_PRIORITY_LAUNCH_SUBURBS:
        positive.append(f"High-priority launch suburb: {lead.get('suburb')}")
        return 25

    if state == "VIC":
        if suburb and suburb in REGIONAL_VIC_SUBURBS:
            positive.append(f"VIC regional area: {lead.get('suburb')}")
            return 10
        if suburb:
            positive.append(f"VIC metro area: {lead.get('suburb')}")
            return 20
        negative.append("VIC state without suburb detail")
        return 10

    if state and state in AU_STATE_CODES:
        positive.append(f"Australian state: {state}")
        return 5

    negative.append("Location outside known AU state codes")
    return 0


def _score_category(
    lead: Mapping[str, Any],
    *,
    positive: list[str],
    negative: list[str],
    warnings: list[str],
) -> int:
    category_raw = lead.get("category")
    if not category_raw:
        warnings.append("Category unknown")
        return 0

    category = str(category_raw).lower()
    for term in STRONG_CATEGORY_TERMS:
        if term in category:
            positive.append(f"Strong category match: {term}")
            return 20

    for term in LIKELY_HOSPITALITY_TERMS:
        if term in category:
            positive.append(f"Likely hospitality venue: {term}")
            return 15

    if any(
        x in category
        for x in ("cafe", "coffee", "retail", "gym", "pharmacy", "bank", "office")
    ):
        warnings.append(f"Category may not be pub/bar fit: {category_raw}")
        negative.append("Category appears non-hospitality")
        return 0

    warnings.append(f"Uncertain category fit: {category_raw}")
    return 8


def _email_safety_class(lead: Mapping[str, Any]) -> str | None:
    if lead.get("email_safety_class"):
        return str(lead["email_safety_class"])
    email = lead.get("email")
    if email:
        return classify_email_contact_safety(str(email))
    return None


def _score_contactability(
    lead: Mapping[str, Any],
    *,
    positive: list[str],
    negative: list[str],
) -> int:
    score = 0
    if lead.get("phone"):
        score += 6
        positive.append("Phone present")
    else:
        negative.append("No phone")

    if lead.get("website"):
        score += 6
        positive.append("Website present")
    else:
        negative.append("No website")

    email = lead.get("email")
    safety = _email_safety_class(lead)
    if email and safety and safety not in _UNSAFE_EMAIL_CLASSES:
        if is_high_confidence_business_email(str(email)) or safety in (
            "generic_business_contact",
            "role_based_contact",
        ):
            score += 5
            positive.append("Safe business email present")
        else:
            score += 2
            positive.append("Business email present (lower confidence)")
    elif email:
        negative.append("Email present but not treated as safe business contact")

    if lead.get("instagram_url") or lead.get("facebook_url"):
        score += 3
        positive.append("Social link present")

    return min(score, 20)


def _score_data_quality(
    lead: Mapping[str, Any],
    *,
    positive: list[str],
    negative: list[str],
    warnings: list[str],
) -> int:
    score = 0
    confidence = int(lead.get("confidence_score") or 0)

    if confidence >= 70:
        score += 5
        positive.append("High import confidence (>=70)")
    elif confidence >= 50:
        score += 3
        positive.append("Moderate import confidence (>=50)")

    address_bits = [
        lead.get("address_line"),
        lead.get("suburb"),
        lead.get("state"),
        lead.get("postcode"),
    ]
    if sum(1 for b in address_bits if b) >= 3:
        score += 2
        positive.append("Address mostly complete")

    if lead.get("latitude") is not None and lead.get("longitude") is not None:
        score += 3
        positive.append("Coordinates present")
    else:
        negative.append("No coordinates")

    source_count = lead.get("source_count")
    if source_count is not None and int(source_count) >= 1:
        score += 2
        positive.append("Has source provenance")

    if lead.get("enrichment_status") == "needs_review":
        score -= 5
        warnings.append("Enrichment status: needs_review")

    if lead.get("suppressed_at"):
        score -= 10
        warnings.append("Lead is suppressed")

    return max(0, min(score, 15))


def _score_product_fit(
    lead: Mapping[str, Any],
    *,
    positive: list[str],
) -> int:
    blob = _text_blob(lead)
    matches = [kw for kw in PRODUCT_FIT_KEYWORDS if kw in blob]
    if matches:
        positive.append(f"Product-fit keywords: {', '.join(matches[:3])}")
        return 10 if len(matches) >= 2 else 8

    category = str(lead.get("category") or "").lower()
    if any(t in category for t in ("pub", "bar", "brewery", "tavern", "hotel")):
        positive.append("Likely pub-discovery fit from category")
        return 5

    return 0


def _score_strategic(
    lead: Mapping[str, Any],
    *,
    positive: list[str],
    negative: list[str],
) -> int:
    score = 0
    name = str(lead.get("name") or "").lower()

    if not any(marker in name for marker in CHAIN_NAME_MARKERS):
        score += 5
        positive.append("Independent-looking venue")
    else:
        negative.append("Possible chain/corporate marker in name")

    if lead.get("website") and (
        lead.get("instagram_url") or lead.get("facebook_url")
    ):
        score += 3
        positive.append("Website and social presence")

    email = lead.get("email")
    if (
        email
        and lead.get("phone")
        and _email_safety_class(lead) == "generic_business_contact"
    ):
        score += 2
        positive.append("Generic email and phone")

    permission = lead.get("contact_permission_status")
    if permission == "do_not_contact":
        score -= 10
        negative.append("Contact permission: do_not_contact")
    elif permission == "opted_out":
        score -= 10
        negative.append("Contact permission: opted_out")

    outreach = lead.get("outreach_status")
    if outreach == "do_not_contact":
        score -= 10
        negative.append("Outreach status: do_not_contact")
    elif outreach == "rejected":
        score -= 10
        negative.append("Outreach status: rejected")

    if lead.get("suppressed_at"):
        score -= 15
        negative.append("Suppressed lead")

    if lead.get("venue_id") and outreach in ("signed_up", "replied"):
        score -= 10
        negative.append("May already be linked to an onboarded venue")

    return score


def compute_founder_fit_score(lead: Mapping[str, Any]) -> FounderFitScoreResult:
    """
    Compute a deterministic founder-fit score (0–100) and explainable breakdown.

    `lead` may include DB column names plus optional `email_safety_class`, `source_count`.
    """
    positive_signals: list[str] = []
    negative_signals: list[str] = []
    if lead.get("enrichment_status") == "enriched":
        warnings: list[str] = ["Includes website-enriched signals where available"]
    else:
        warnings = ["Imported data only; website enrichment not applied or pending review"]

    location = _score_location(
        lead, positive=positive_signals, negative=negative_signals
    )
    category = _score_category(
        lead,
        positive=positive_signals,
        negative=negative_signals,
        warnings=warnings,
    )
    contactability = _score_contactability(
        lead, positive=positive_signals, negative=negative_signals
    )
    data_quality = _score_data_quality(
        lead,
        positive=positive_signals,
        negative=negative_signals,
        warnings=warnings,
    )
    product_fit = _score_product_fit(lead, positive=positive_signals)
    strategic = _score_strategic(
        lead, positive=positive_signals, negative=negative_signals
    )

    raw_total = (
        location
        + category
        + contactability
        + data_quality
        + product_fit
        + strategic
    )
    final_score = max(0, min(100, raw_total))

    breakdown: dict[str, Any] = {
        "score": final_score,
        "components": {
            "location": location,
            "category": category,
            "contactability": contactability,
            "data_quality": data_quality,
            "product_fit": product_fit,
            "strategic": strategic,
        },
        "positive_signals": positive_signals,
        "negative_signals": negative_signals,
        "warnings": warnings,
        "launch_relevance_score": location,
        "category_score": category,
        "contactability_score": contactability,
        "data_quality_score": data_quality,
        "product_fit_score": product_fit,
    }

    return FounderFitScoreResult(score=final_score, breakdown=breakdown)
