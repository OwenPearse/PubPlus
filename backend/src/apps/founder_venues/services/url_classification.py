"""Classify and normalize venue vs social URLs for import and cleanup."""

from __future__ import annotations

from urllib.parse import urlparse

from apps.founder_venues.services.normalization import normalize_website_url, website_host

FACEBOOK_HOSTS = frozenset(
    {
        "facebook.com",
        "www.facebook.com",
        "m.facebook.com",
        "fb.com",
        "www.fb.com",
    }
)

INSTAGRAM_HOSTS = frozenset(
    {
        "instagram.com",
        "www.instagram.com",
        "instagr.am",
        "www.instagr.am",
    }
)

OTHER_SOCIAL_HOSTS = frozenset(
    {
        "twitter.com",
        "www.twitter.com",
        "x.com",
        "www.x.com",
        "tiktok.com",
        "www.tiktok.com",
        "linkedin.com",
        "www.linkedin.com",
        "youtube.com",
        "www.youtube.com",
    }
)

NON_VENUE_WEBSITE_HOSTS = frozenset(
    {
        "linktr.ee",
        "www.linktr.ee",
        "tripadvisor.com",
        "www.tripadvisor.com",
        "yelp.com",
        "www.yelp.com",
        "bit.ly",
        "t.co",
        "goo.gl",
        "maps.app.goo.gl",
    }
)

SOCIAL_BLOCK_PATH_MARKERS = (
    "/sharer",
    "/share.php",
    "/login",
    "/dialog/",
    "/intent/",
    "/plugins/",
    "sharer.php",
    "/accounts/login",
)


def _host_key(url: str) -> str | None:
    host = website_host(url)
    if not host:
        return None
    return host.lower().removeprefix("www.")


def _is_blocked_social_path(url: str) -> bool:
    lower = url.lower()
    return any(marker in lower for marker in SOCIAL_BLOCK_PATH_MARKERS)


def _is_google_maps(url: str, host: str) -> bool:
    lower = url.lower()
    if host == "maps.google.com" or host.endswith(".google.com") and "/maps" in lower:
        return True
    return "google.com/maps" in lower


def _facebook_profile_path(parsed) -> bool:
    path = (parsed.path or "").strip("/")
    if not path:
        return False
    if path in ("login.php", "home.php", "pages", "groups"):
        return False
    return True


def _instagram_profile_path(parsed) -> bool:
    path = (parsed.path or "").strip("/")
    if not path or path in ("accounts", "explore", "p"):
        return False
    return True


def classify_url_kind(url: str | None) -> str:
    """
    Return: website | instagram | facebook | other_social | invalid | empty
    """
    if url is None or not str(url).strip():
        return "empty"

    normalized = normalize_website_url(url)
    if not normalized:
        return "invalid"

    if _is_blocked_social_path(normalized):
        return "invalid"

    host = _host_key(normalized)
    if not host:
        return "invalid"

    parsed = urlparse(normalized)

    if host in FACEBOOK_HOSTS or host.endswith(".facebook.com") or host == "fb.com":
        return "facebook" if _facebook_profile_path(parsed) else "invalid"

    if host in INSTAGRAM_HOSTS or host.endswith(".instagram.com"):
        return "instagram" if _instagram_profile_path(parsed) else "invalid"

    if host in OTHER_SOCIAL_HOSTS:
        return "other_social"

    if host in NON_VENUE_WEBSITE_HOSTS:
        return "invalid"

    if _is_google_maps(normalized, host):
        return "invalid"

    return "website"


def is_social_profile_url(url: str | None) -> bool:
    return classify_url_kind(url) in ("facebook", "instagram", "other_social")


def normalize_social_url(url: str | None) -> str | None:
    """Normalize Facebook or Instagram profile URL; None if not a valid profile."""
    kind = classify_url_kind(url)
    if kind not in ("facebook", "instagram"):
        return None

    normalized = normalize_website_url(url)
    if not normalized or _is_blocked_social_path(normalized):
        return None

    parsed = urlparse(normalized)
    path = parsed.path.rstrip("/") or ""

    if kind == "instagram":
        if not _instagram_profile_path(parsed):
            return None
        return f"https://www.instagram.com{path}/"

    if not _facebook_profile_path(parsed):
        return None
    return f"https://www.facebook.com{path}/"


def website_url_is_fetchable(url: str | None) -> bool:
    """True when URL is a real venue website suitable for Stage 6 fetch."""
    return classify_url_kind(url) == "website"


def apply_import_url_routing(
    *,
    website: str | None,
    facebook_url: str | None,
    instagram_url: str | None,
) -> tuple[str | None, str | None, str | None]:
    """
    Route social URLs out of website into social fields.

    Does not overwrite existing facebook_url / instagram_url.
    """
    fb = normalize_social_url(facebook_url) if facebook_url else None
    ig = normalize_social_url(instagram_url) if instagram_url else None

    if website:
        kind = classify_url_kind(website)
        social_norm = normalize_social_url(website)
        if kind == "facebook" and not fb and social_norm:
            fb = social_norm
            website = None
        elif kind == "instagram" and not ig and social_norm:
            ig = social_norm
            website = None
        elif kind == "website":
            website = normalize_website_url(website)
        else:
            website = None

    return website, fb, ig
