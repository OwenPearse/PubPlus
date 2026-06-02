"""Conservative same-origin website fetching for founder venue enrichment."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from apps.founder_venues.services.normalization import normalize_website_url, website_host

USER_AGENT = "PubPlus-FounderVenueEnrichment/1.0 (+https://pubplus.app; internal research)"
REQUEST_TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 1_048_576
MAX_PAGES_PER_LEAD = 5
MAX_EXTRA_PAGES = 4
MAX_REDIRECTS = 5
DOMAIN_MIN_INTERVAL_SECONDS = 1.0

ALLOWED_HTML_CONTENT_TYPES = frozenset(
    {
        "text/html",
        "application/xhtml+xml",
    }
)

BLOCKED_PATH_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".zip",
    ".doc",
    ".docx",
)

PATH_KEYWORDS = (
    "contact",
    "about",
    "function",
    "functions",
    "events",
    "whats-on",
    "whatson",
    "bookings",
    "book",
    "venue",
    "private-events",
    "sport",
    "sports",
    "trivia",
    "live-music",
)

SOCIAL_FETCH_HOSTS = frozenset(
    {
        "instagram.com",
        "www.instagram.com",
        "facebook.com",
        "www.facebook.com",
        "m.facebook.com",
        "fb.com",
        "www.fb.com",
        "twitter.com",
        "x.com",
        "tiktok.com",
        "linkedin.com",
    }
)

HREF_PATTERN = re.compile(
    r"""<a\s+[^>]*href\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)

_domain_last_fetch: dict[str, float] = {}


@dataclass(frozen=True)
class FetchedPage:
    url: str
    html: str


@dataclass(frozen=True)
class FetchPageResult:
    url: str
    html: str | None
    error: str | None = None


PageFetcher = Callable[[str], FetchPageResult]


def reset_domain_throttle_for_tests() -> None:
    _domain_last_fetch.clear()


from apps.founder_venues.services.url_classification import (
    is_social_profile_url,
    website_url_is_fetchable,
)


def is_allowed_fetch_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.netloc or "").lower()
    if not host:
        return False
    if host.startswith("www."):
        host = host[4:]
    if host in SOCIAL_FETCH_HOSTS:
        return False
    path_lower = (parsed.path or "").lower()
    for ext in BLOCKED_PATH_EXTENSIONS:
        if path_lower.endswith(ext):
            return False
    return True


def _path_keyword_score(path: str) -> int:
    lower = path.lower()
    score = 0
    for keyword in PATH_KEYWORDS:
        if keyword in lower:
            score += 10
    return score


def select_same_origin_page_urls(
    homepage_url: str,
    html: str,
    *,
    max_extra: int = MAX_EXTRA_PAGES,
) -> list[str]:
    """Return up to max_extra same-origin URLs matching allowlisted path keywords."""
    home = normalize_website_url(homepage_url)
    if not home:
        return []
    home_host = website_host(home)
    if not home_host:
        return []

    candidates: dict[str, int] = {}
    for href in HREF_PATTERN.findall(html):
        absolute = urljoin(home, href.strip())
        if not is_allowed_fetch_url(absolute):
            continue
        normalized = normalize_website_url(absolute)
        if not normalized or normalized == home:
            continue
        host = website_host(normalized)
        if host != home_host:
            continue
        score = _path_keyword_score(urlparse(normalized).path or "")
        if score <= 0:
            continue
        existing = candidates.get(normalized)
        if existing is None or score > existing:
            candidates[normalized] = score

    ranked = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))
    return [url for url, _ in ranked[:max_extra]]


def _throttle_domain(host: str) -> None:
    now = time.monotonic()
    last = _domain_last_fetch.get(host)
    if last is not None:
        elapsed = now - last
        if elapsed < DOMAIN_MIN_INTERVAL_SECONDS:
            time.sleep(DOMAIN_MIN_INTERVAL_SECONDS - elapsed)
    _domain_last_fetch[host] = time.monotonic()


def _read_limited_body(response, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        block = response.read(min(65536, max_bytes - total))
        if not block:
            break
        chunks.append(block)
        total += len(block)
        if total >= max_bytes:
            break
    return b"".join(chunks)


def default_fetch_page(url: str) -> FetchPageResult:
    if not is_allowed_fetch_url(url):
        return FetchPageResult(url=url, html=None, error="URL not allowed for fetch")

    current = normalize_website_url(url)
    if not current:
        return FetchPageResult(url=url, html=None, error="Invalid URL")

    host = website_host(current)
    if host:
        _throttle_domain(host)

    for _ in range(MAX_REDIRECTS + 1):
        try:
            request = Request(
                current,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            )
            with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                content_type = (response.headers.get_content_type() or "").split(";")[0].strip().lower()
                if content_type and content_type not in ALLOWED_HTML_CONTENT_TYPES:
                    return FetchPageResult(
                        url=current,
                        html=None,
                        error=f"Unsupported content type: {content_type}",
                    )
                body = _read_limited_body(response, MAX_RESPONSE_BYTES)
                charset = response.headers.get_content_charset() or "utf-8"
                try:
                    html = body.decode(charset, errors="replace")
                except LookupError:
                    html = body.decode("utf-8", errors="replace")
                return FetchPageResult(url=current, html=html)
        except HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
                location = exc.headers.get("Location")
                current = normalize_website_url(urljoin(current, location))
                if not current or not is_allowed_fetch_url(current):
                    return FetchPageResult(url=url, html=None, error="Redirect to disallowed URL")
                continue
            return FetchPageResult(url=current, html=None, error=f"HTTP {exc.code}")
        except URLError as exc:
            return FetchPageResult(url=current, html=None, error=str(exc.reason))
        except TimeoutError:
            return FetchPageResult(url=current, html=None, error="Request timed out")
        except OSError as exc:
            return FetchPageResult(url=current, html=None, error=str(exc))

    return FetchPageResult(url=url, html=None, error="Too many redirects")


def fetch_venue_website_pages(
    website_url: str,
    *,
    page_fetcher: PageFetcher | None = None,
) -> tuple[list[FetchedPage], list[str], list[str]]:
    """
    Fetch homepage and up to MAX_EXTRA_PAGES allowlisted same-origin pages.

    Returns (pages, fetched_urls, errors).
    """
    fetcher = page_fetcher or default_fetch_page
    home = normalize_website_url(website_url)
    if not home:
        return [], [], ["Invalid website URL"]

    pages: list[FetchedPage] = []
    fetched_urls: list[str] = []
    errors: list[str] = []

    home_result = fetcher(home)
    if home_result.html:
        pages.append(FetchedPage(url=home_result.url, html=home_result.html))
        fetched_urls.append(home_result.url)
        extra_urls = select_same_origin_page_urls(home_result.url, home_result.html)
    else:
        errors.append(home_result.error or f"Failed to fetch homepage: {home}")
        return pages, fetched_urls, errors

    for extra_url in extra_urls:
        if len(pages) >= MAX_PAGES_PER_LEAD:
            break
        extra_result = fetcher(extra_url)
        if extra_result.html:
            pages.append(FetchedPage(url=extra_result.url, html=extra_result.html))
            fetched_urls.append(extra_result.url)
        elif extra_result.error:
            errors.append(f"{extra_url}: {extra_result.error}")

    return pages, fetched_urls, errors
