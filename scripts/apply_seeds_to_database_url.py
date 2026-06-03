"""
Apply Supabase migrations + dev seeds (from database/supabase/seed.sql order) to Postgres.
Uses DATABASE_URL from database/.env; fixes db.<project-ref> using SUPABASE_URL. Never prints secrets.
Requires: pip install psycopg sqlparse
"""
from __future__ import annotations

import re
import socket
import subprocess
import sys
import urllib.parse
from pathlib import Path

import psycopg
import sqlparse

REPO = Path(__file__).resolve().parents[1]
ENV_FILE = REPO / "database" / ".env"
MIGRATIONS = REPO / "database" / "supabase" / "migrations"
SEEDS = [
    REPO / "database" / "sql" / "seeds" / "dev_seed_reference_minimum.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_reference_melbourne_localities.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_demo_venues.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_demo_accounts_and_relationships.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_melbourne_inner_venues.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_demo_specials.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_melbourne_inner_specials.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_demo_taps.sql",
    REPO / "database" / "sql" / "seeds" / "dev_seed_demo_commercial.sql",
]


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
    if not u:
        print("ERROR: DATABASE_URL missing in database/.env", file=sys.stderr)
        sys.exit(1)
    if "db.<project-ref>.supabase.co" in u and "SUPABASE_URL" in env:
        m = re.search(r"https://([a-z0-9]+)\.supabase\.co", env["SUPABASE_URL"])
        if m:
            u = u.replace("db.<project-ref>.supabase.co", f"db.{m.group(1)}.supabase.co")
    if "supabase.co" in u and "sslmode" not in u:
        u = u + ("&" if "?" in u else "?") + "sslmode=require"
    return u


def _resolve_host_windows(h: str) -> str | None:
    """If Python getaddrinfo fails (common with IPv6-only AAAA for Supabase), use PowerShell."""
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
    """
    Some Supabase direct hosts are IPv6-only. Resolve the hostname and pass
    a numeric address so some Windows/Python combinations can connect.
    """
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


def _stmts(path: Path) -> list[str]:
    out: list[str] = []
    for raw in sqlparse.split(path.read_text(encoding="utf-8")):
        stmt = raw.strip()
        if not stmt:
            continue
        low = stmt.rstrip(";").strip().lower()
        if low in ("begin", "commit"):
            continue
        out.append(stmt)
    return out


def _exec_idempotent(
    conn: psycopg.Connection, stmt: str, tag: str
) -> None:
    try:
        conn.execute(stmt)
    except Exception as e:
        msg = str(e).lower()
        if any(
            x in msg
            for x in (
                "already exists",
                "duplicate",
                "unique constraint",
            )
        ):
            print("  skip:", tag, flush=True)
            return
        raise


def main() -> None:
    if not ENV_FILE.is_file():
        print("ERROR: database/.env not found", file=sys.stderr)
        sys.exit(1)
    dsn = resolve_database_url(load_env(ENV_FILE))
    with connect_from_env(dsn) as conn:
        conn.autocommit = True
        conn.execute("select 1")
        print("connected", flush=True)
        for f in sorted(MIGRATIONS.glob("*.sql"), key=lambda p: p.name):
            print("migration:", f.name, flush=True)
            for i, stmt in enumerate(_stmts(f)):
                _exec_idempotent(conn, stmt, f.name + f"#{i}")
        for p in SEEDS:
            if not p.is_file():
                print("missing seed", p, file=sys.stderr)
                sys.exit(1)
            print("seed:", p.name, flush=True)
            for i, stmt in enumerate(_stmts(p)):
                _exec_idempotent(conn, stmt, p.name + f"#{i}")
    print("done", flush=True)


if __name__ == "__main__":
    main()
