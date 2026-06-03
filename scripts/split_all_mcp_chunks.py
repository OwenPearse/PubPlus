"""Split each _mcp_apply_chunks/*.sql into statement batches (max size) under _mcp_apply_tiny/."""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

import sqlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "database" / "sql" / "seeds" / "_mcp_apply_chunks"
OUT = ROOT / "database" / "sql" / "seeds" / "_mcp_apply_tiny"
MAXC = 5000


def split_file(path: Path, maxc: int) -> list[str]:
    stmts: list[str] = []
    for raw in sqlparse.split(path.read_text(encoding="utf-8")):
        s = raw.strip()
        if not s:
            continue
        low = s.rstrip(";").strip().lower()
        if low in ("begin", "commit"):
            continue
        stmts.append(s)
    buf: list[str] = []
    nchars = 0
    parts: list[str] = []
    for s in stmts:
        slen = len(s) + 2
        if buf and nchars + slen > maxc:
            parts.append("\n\n".join(buf) + "\n")
            buf, nchars = [], 0
        buf.append(s)
        nchars += slen
    if buf:
        parts.append("\n\n".join(buf) + "\n")
    return parts


def main() -> int:
    if not SRC.is_dir():
        print("missing", SRC, file=sys.stderr)
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    def sort_key(p: Path) -> tuple:
        m = re.match(r"^(venues|specials)_(\d+)", p.stem)
        if not m:
            return (99, 99, p.name)
        g = 0 if m.group(1) == "venues" else 1
        return (g, int(m.group(2)), p.name)

    order: list[Path] = []
    for name in sorted(
        [p for p in SRC.iterdir() if p.suffix == ".sql"],
        key=sort_key,
    ):
        if not re.match(r"^(venues|specials)_\d+\.sql$", name.name):
            continue
        parts = split_file(name, MAXC)
        print(f"{name.name} -> {len(parts)} part(s)", file=sys.stderr)
        for i, text in enumerate(parts, start=1):
            out = OUT / f"{name.stem}_{i:02d}.sql"
            out.write_text(text, encoding="utf-8")
            order.append(out)
    (OUT / "_order.txt").write_text(
        "\n".join(p.name for p in order) + "\n", encoding="utf-8"
    )
    for p in order:
        print(p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
