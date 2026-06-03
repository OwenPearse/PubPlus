"""Print concatenation of N tiny SQL parts from _mcp_apply_tiny (UTF-8) for execute_sql."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "database" / "sql" / "seeds" / "_mcp_apply_tiny"


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    names = (ROOT / "_order.txt").read_text(encoding="utf-8").split()
    sub = names[start : start + n]
    if not sub:
        return 0
    parts: list[str] = []
    for name in sub:
        parts.append((ROOT / name).read_text(encoding="utf-8"))
    sys.stdout.buffer.write(("\n\n".join(parts) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
