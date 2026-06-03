"""Split a .sql file into statement batches (max size) for MCP execute_sql. Strips begin/commit."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import sqlparse


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: split_sql_for_mcp.py <file.sql> [max_chars]", file=sys.stderr)
        sys.exit(1)
    path = Path(sys.argv[1])
    maxc = int(sys.argv[2]) if len(sys.argv) > 2 else 45000
    out_dir = Path(tempfile.mkdtemp(prefix="mcpseed_"))
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
    part = 0
    for s in stmts:
        slen = len(s) + 2
        if buf and nchars + slen > maxc:
            part += 1
            fp = out_dir / f"chunk_{part:02d}.sql"
            fp.write_text("\n\n".join(buf) + "\n", encoding="utf-8")
            print(f"{fp}", flush=True)
            buf, nchars = [], 0
        buf.append(s)
        nchars += slen
    if buf:
        part += 1
        fp = out_dir / f"chunk_{part:02d}.sql"
        fp.write_text("\n\n".join(buf) + "\n", encoding="utf-8")
        print(f"{fp}", flush=True)
    print(f"OUT_DIR={out_dir}", file=sys.stderr)
    print(f"parts={part} stmts={len(stmts)}", file=sys.stderr)


if __name__ == "__main__":
    main()
