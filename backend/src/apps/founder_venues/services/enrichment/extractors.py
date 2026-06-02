"""HTML extraction helpers for venue website enrichment (pure functions)."""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin, urlparse

from apps.founder_venues.services.contact_safety import classify_email_contact_safety
from apps.founder_venues.services.enrichment.result import WebsiteEnrichmentCandidate
from apps.founder_venues.services.normalization import (
    normalize_email,
    normalize_phone_au,
    normalize_website_url,
)

EMAIL_PATTERN = re.compile(
    r"\b[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}\b"
)
MAILTO_PATTERN = re.compile(
    r"mailto:([a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})",
    re.IGNORECASE,
)
TEL_PATTERN = re.compile(r"tel:([+\d\s().-]+)", re.IGNORECASE)
HREF_PATTERN = re.compile(
    r"""<a\s+[^>]*href\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")

DISALLOWED_EMAIL_LOCALS = frozenset(
    {
        "noreply",
        "no-reply",
        "donotreply",
        "do-not-reply",
        "mailer-daemon",
        "postmaster",
    }
)
DISALLOWED_EMAIL_DOMAINS = frozenset(
    {
        "example.com",
        "example.org",
        "example.net",
        "test.com",
        "invalid",
        "localhost",
    }
)

PROMOTABLE_EMAIL_SAFETY = frozenset(
    {"generic_business_contact", "role_based_contact"}
)

PRODUCT_SIGNAL_TERMS: tuple[tuple[str, str], ...] = (
    ("trivia", "trivia"),
    ("quiz night", "quiz night"),
    ("live music", "live music"),
    ("dj", "dj"),
    ("rooftop", "rooftop"),
    ("beer garden", "beer garden"),
    ("craft beer", "craft beer"),
    ("brewery", "brewery"),
    ("functions", "functions"),
    ("private events", "private events"),
    ("private-events", "private events"),
    ("events", "events"),
    ("happy hour", "happy hour"),
    ("specials", "specials"),
    ("parma", "parma"),
    ("steak night", "steak night"),
    ("comedy", "comedy"),
    ("open mic", "open mic"),
    ("sports bar", "sports bar"),
    ("sport", "sport"),
    ("sports", "sports"),
    ("afl", "AFL"),
    ("ufc", "UFC"),
    ("tab", "TAB"),
    ("whats-on", "whats-on"),
    ("whatson", "whatson"),
)

INSTAGRAM_HOSTS = frozenset({"instagram.com", "www.instagram.com"})
FACEBOOK_HOSTS = frozenset(
    {"facebook.com", "www.facebook.com", "m.facebook.com", "fb.com", "www.fb.com"}
)

SOCIAL_BLOCK_PATH_MARKERS = (
    "/sharer",
    "/share.php",
    "/login",
    "/dialog/",
    "/intent/",
    "/plugins/",
    "sharer.php",
)


def strip_html_to_text(html: str) -> str:
    without_blocks = SCRIPT_STYLE_RE.sub(" ", html)
    without_tags = TAG_RE.sub(" ", without_blocks)
    return unescape(_collapse_ws(without_tags))


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _email_domain(email: str) -> str:
    return email.rpartition("@")[2].lower()


def _is_fake_email(email: str) -> bool:
    local, _, domain = email.partition("@")
    local = local.lower()
    domain = domain.lower()
    if domain in DISALLOWED_EMAIL_DOMAINS:
        return True
    if local in DISALLOWED_EMAIL_LOCALS:
        return True
    if domain.endswith(".example") or domain.endswith(".test"):
        return True
    if "sentry" in domain or "wixpress" in domain:
        return True
    return False


def email_on_venue_domain(email: str, venue_host: str | None) -> bool:
    if not venue_host:
        return False
    domain = _email_domain(email)
    host = venue_host.lower().removeprefix("www.")
    return domain == host or domain.endswith(f".{host}")


def email_candidate_confidence(
    *,
    safety_class: str | None,
    same_venue_domain: bool,
) -> int:
    if safety_class in PROMOTABLE_EMAIL_SAFETY:
        return 85 if same_venue_domain else 65
    if safety_class == "personal_business_contact":
        return 45
    if safety_class == "likely_personal_or_unsafe":
        return 20
    return 40


def is_email_auto_promotable(safety_class: str | None) -> bool:
    return safety_class in PROMOTABLE_EMAIL_SAFETY


def extract_emails_from_html(
    html: str,
    *,
    source_url: str,
    venue_host: str | None,
    contact_page: bool = False,
) -> list[WebsiteEnrichmentCandidate]:
    found: dict[str, WebsiteEnrichmentCandidate] = {}
    text = strip_html_to_text(html)
    sources: list[str] = []
    for match in MAILTO_PATTERN.finditer(html):
        sources.append(match.group(1))
    sources.extend(EMAIL_PATTERN.findall(text))

    for raw in sources:
        normalized = normalize_email(raw)
        if not normalized or _is_fake_email(normalized):
            continue
        safety = classify_email_contact_safety(normalized)
        same_domain = email_on_venue_domain(normalized, venue_host)
        confidence = email_candidate_confidence(
            safety_class=safety, same_venue_domain=same_domain
        )
        if contact_page and safety in PROMOTABLE_EMAIL_SAFETY:
            confidence = min(95, confidence + 5)
        key = normalized
        candidate = WebsiteEnrichmentCandidate(
            field_name="email",
            raw_value=raw,
            normalized_value=normalized,
            source_url=source_url,
            confidence=confidence,
            contact_safety_class=safety,
        )
        existing = found.get(key)
        if existing is None or candidate.confidence > existing.confidence:
            found[key] = candidate
    return list(found.values())


def extract_phones_from_html(
    html: str,
    *,
    source_url: str,
    contact_page: bool = False,
) -> list[WebsiteEnrichmentCandidate]:
    found: dict[str, WebsiteEnrichmentCandidate] = {}
    text = strip_html_to_text(html)
    raw_candidates: list[str] = []
    for match in TEL_PATTERN.finditer(html):
        raw_candidates.append(match.group(1))
    raw_candidates.extend(
        re.findall(r"(?:\+61|0)[\d\s().-]{8,14}", text)
    )

    for raw in raw_candidates:
        normalized = normalize_phone_au(raw)
        if not normalized:
            continue
        confidence = 80 if contact_page else 70
        candidate = WebsiteEnrichmentCandidate(
            field_name="phone",
            raw_value=raw.strip(),
            normalized_value=normalized,
            source_url=source_url,
            confidence=confidence,
        )
        existing = found.get(normalized)
        if existing is None or candidate.confidence > existing.confidence:
            found[normalized] = candidate
    return list(found.values())


def _is_blocked_social_href(url: str) -> bool:
    lower = url.lower()
    return any(marker in lower for marker in SOCIAL_BLOCK_PATH_MARKERS)


def _normalize_social_url(href: str, base_url: str) -> str | None:
    absolute = urljoin(base_url, href.strip())
    parsed = urlparse(absolute)
    if parsed.scheme not in ("http", "https"):
        return None
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/") or ""
    if _is_blocked_social_href(absolute):
        return None
    if host in INSTAGRAM_HOSTS:
        if not path or path in ("/", "/accounts", "/explore"):
            return None
        return f"https://www.instagram.com{path}/"
    if host in FACEBOOK_HOSTS or host == "fb.com":
        if not path or path in ("/", "/login.php", "/home.php"):
            return None
        return f"https://www.facebook.com{path}/"
    return None


def extract_social_links_from_html(
    html: str,
    *,
    source_url: str,
) -> list[WebsiteEnrichmentCandidate]:
    found: dict[tuple[str, str], WebsiteEnrichmentCandidate] = {}
    for href in HREF_PATTERN.findall(html):
        normalized = _normalize_social_url(href, source_url)
        if not normalized:
            continue
        host = urlparse(normalized).netloc.lower()
        if "instagram" in host:
            field_name = "instagram_url"
        elif "facebook" in host or "fb.com" in host:
            field_name = "facebook_url"
        else:
            continue
        key = (field_name, normalized)
        candidate = WebsiteEnrichmentCandidate(
            field_name=field_name,
            raw_value=href,
            normalized_value=normalized,
            source_url=source_url,
            confidence=75,
        )
        if key not in found:
            found[key] = candidate
    return list(found.values())


def extract_product_signals_from_html(html: str) -> list[str]:
    text = strip_html_to_text(html).lower()
    signals: list[str] = []
    seen: set[str] = set()
    for needle, label in PRODUCT_SIGNAL_TERMS:
        if needle in text and label not in seen:
            seen.add(label)
            signals.append(label)
    return signals


def extract_contact_page_url(
    html: str,
    *,
    source_url: str,
    venue_host: str | None,
) -> WebsiteEnrichmentCandidate | None:
    if not venue_host:
        return None
    for href in HREF_PATTERN.findall(html):
        absolute = urljoin(source_url, href.strip())
        parsed = urlparse(absolute)
        if (parsed.netloc or "").lower().removeprefix("www.") != venue_host.lower().removeprefix(
            "www."
        ):
            continue
        path_lower = (parsed.path or "").lower()
        if "contact" in path_lower:
            normalized = normalize_website_url(absolute)
            if normalized:
                return WebsiteEnrichmentCandidate(
                    field_name="contact_page_url",
                    raw_value=href,
                    normalized_value=normalized,
                    source_url=source_url,
                    confidence=70,
                )
    return None
