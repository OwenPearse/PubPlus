"""Run Stage 3 verification queries using database/.env (no secrets printed)."""
from __future__ import annotations

import re
import socket
import subprocess
import sys
import urllib.parse
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
ENV_FILE = REPO / "database" / ".env"


def load_env(path: Path) -> dict[str, str]:
    d: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        d[k.strip()] = v.strip()
    return d


def resolve_database_url(env: dict[str, str]) -> str:
    u = env.get("DATABASE_URL", "").strip()
    if "db.<project-ref>.supabase.co" in u and "SUPABASE_URL" in env:
        m = re.search(r"https://([a-z0-9]+)\.supabase\.co", env["SUPABASE_URL"])
        if m:
            u = u.replace("db.<project-ref>.supabase.co", f"db.{m.group(1)}.supabase.co")
    if "supabase.co" in u and "sslmode" not in u:
        u = u + ("&" if "?" in u else "?") + "sslmode=require"
    return u


def _resolve_host_windows(h: str) -> str | None:
    for rtype in ("A", "AAAA"):
        try:
            out = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Resolve-DnsName {h!r} -Type {rtype} -ErrorAction SilentlyContinue | "
                    f"Select-Object -First 1 -ExpandProperty IPAddress)",
                ],
                text=True,
                timeout=15,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
            continue
        if out and (":" in out or re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", out)):
            return out
    return None


def connect_from_env(dsn: str) -> psycopg.Connection:
    p = urllib.parse.urlparse(dsn)
    host = p.hostname
    if not host:
        return psycopg.connect(dsn, connect_timeout=30)
    port = p.port or 5432
    dbn = (p.path or "/postgres").lstrip("/") or "postgres"
    user = urllib.parse.unquote(p.username) if p.username else "postgres"
    pwd = urllib.parse.unquote(p.password) if p.password else ""
    iph: str | None = None
    for family in (socket.AF_INET6, socket.AF_INET):
        try:
            res = socket.getaddrinfo(
                host,
                port,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
                family=family,
            )
        except OSError:
            res = []
        for r in res:
            _fa, _ty, _pr, _ca, sa = r
            iph = sa[0]
            break
        if iph:
            break
    if not iph and sys.platform == "win32":
        iph = _resolve_host_windows(host)
    if not iph:
        return psycopg.connect(dsn, connect_timeout=30)
    return psycopg.connect(
        host=iph,
        port=port,
        dbname=dbn,
        user=user,
        password=pwd,
        sslmode="require",
        connect_timeout=30,
    )


def main() -> None:
    dsn = resolve_database_url(load_env(ENV_FILE))
    with connect_from_env(dsn) as conn:
        conn.autocommit = True
        q = [
            (
                "richmond_count",
                """
            select count(*) from public.venue v
            join public.venue_published_location vpl on vpl.venue_id = v.id
            join public.locality l on l.id = vpl.locality_id
            where lower(l.name) = lower('Richmond') and v.id::text like 'f1111111-1111-4111-8111-0000%'
            """,
            ),
            (
                "viewport_count",
                """
            select count(*) from public.venue v
            join public.venue_published_map_point m on m.venue_id = v.id
            where v.id::text like 'f1111111-1111-4111-8111-0000%'
              and m.latitude::float8 between -37.87 and -37.76
              and m.longitude::float8 between 144.92 and 145.05
            """,
            ),
            (
                "venue_001",
                """
            select p.display_name, l.name
            from public.venue v
            join public.venue_published_profile p on p.venue_id = v.id
            join public.venue_published_location vpl on vpl.venue_id = v.id
            join public.locality l on l.id = vpl.locality_id
            where v.id = 'f1111111-1111-4111-8111-000000000001'
            """,
            ),
            (
                "late_night",
                """
            select count(*) from public.venue_hours_regular h
            join public.venue v on v.id = h.venue_id
            where v.id::text like 'f1111111-1111-4111-8111-0000%' and h.crosses_midnight
            """,
            ),
            (
                "exceptions",
                """
            select count(*) from public.venue_hours_exception e
            where e.venue_id::text like 'f1111111-1111-4111-8111-0000%'
            """,
            ),
            (
                "partial_uncertainty",
                """
            select count(*) from public.venue_hours_uncertainty u
            where u.venue_id::text like 'f1111111-1111-4111-8111-0000%' and u.uncertainty_level = 'partial'
            """,
            ),
            (
                "melbourne_specials",
                """
            select count(*) from public.venue_published_structured_special s
            where s.venue_id::text like 'f1111111-1111-4111-8111-0000%'
            """,
            ),
        ]
        for name, sql in q:
            cur = conn.execute(sql)
            row = cur.fetchone()
            print(f"{name}:", row[0] if row else None, flush=True)


if __name__ == "__main__":
    main()
