import os
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(dotenv_path: Path | None = None) -> None:
    env_file = dotenv_path or (BASE_DIR / ".env")
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value or ""


def get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_postgres_netloc(netloc: str) -> tuple[str, str, str, int]:
    """
    Split userinfo and host:port without urllib's username/password/netloc rules.

    Passwords may contain ``@`` and ``:`` when unescaped in PaaS env vars; the
    last ``@`` separates credentials from ``host:port``, and the first ``:`` in
    credentials separates user from password.
    """
    if "@" in netloc:
        userinfo, hostport = netloc.rsplit("@", 1)
    else:
        userinfo, hostport = "", netloc

    if ":" in userinfo:
        user, password = userinfo.split(":", 1)
    else:
        user, password = userinfo, ""

    host = hostport
    port = 5432
    if hostport.startswith("["):
        bracket_end = hostport.find("]")
        if bracket_end != -1 and len(hostport) > bracket_end + 1 and hostport[bracket_end + 1] == ":":
            host = hostport[: bracket_end + 1]
            port_str = hostport[bracket_end + 2 :]
        else:
            port_str = None
    elif ":" in hostport:
        host, port_str = hostport.rsplit(":", 1)
    else:
        port_str = None

    if port_str is not None:
        if not re.fullmatch(r"\d+", port_str):
            raise ValueError(
                f"DATABASE_URL port must be numeric; got {port_str!r}. "
                "Percent-encode special characters in the password, or unset "
                "DATABASE_URL and use DB_HOST / DB_PORT / DB_USER / DB_PASSWORD."
            )
        port = int(port_str)

    return unquote(user), unquote(password), unquote(host), port


def parse_database_url(database_url: str) -> dict[str, str | int | dict[str, str]]:
    url = database_url.strip()
    if not url:
        raise RuntimeError("Empty DATABASE_URL")

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme in {"postgres", "postgresql"}:
        if not parsed.netloc:
            raise RuntimeError("DATABASE_URL is missing a host")
        try:
            user, password, host, port = _parse_postgres_netloc(parsed.netloc)
        except ValueError:
            raise
        db_name = unquote(parsed.path.lstrip("/")) or "postgres"
        config: dict[str, str | int | dict[str, str]] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": user,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
        }
        query = parse_qs(parsed.query)
        sslmode = (query.get("sslmode") or [None])[0]
        if sslmode:
            config["OPTIONS"] = {"sslmode": sslmode}
        return config
    if scheme == "sqlite":
        sqlite_path = parsed.path
        if sqlite_path in {"", "/"}:
            sqlite_path = str(BASE_DIR / "db.sqlite3")
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": sqlite_path}
    raise RuntimeError(
        "Unsupported DATABASE_URL scheme. Use postgresql:// or sqlite:///"
    )
