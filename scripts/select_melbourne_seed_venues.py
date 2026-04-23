"""Select 28 diverse inner-Melbourne rows; export JSON for seeds."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "dataCollection" / "Pub_Australia.csv"
OUT_JSON = ROOT / "dataCollection" / "melbourne_inner_seed_venues.json"

ALLOW = {
    "brunswick",
    "brunswick west",
    "carlton",
    "carlton north",
    "collingwood",
    "fitzroy",
    "fitzroy north",
    "abbotsford",
    "richmond",
    "hawthorn",
    "prahran",
    "south yarra",
    "windsor",
    "st kilda",
    "st kilda west",
    "melbourne",
    "east melbourne",
    "west melbourne",
    "docklands",
    "south melbourne",
    "port melbourne",
    "cremorne",
    "clifton hill",
}

PRIORITY = [
    "Brunswick",
    "Brunswick West",
    "Carlton",
    "Carlton North",
    "Collingwood",
    "Fitzroy",
    "Fitzroy North",
    "Abbotsford",
    "Richmond",
    "South Yarra",
    "Hawthorn",
    "Prahran",
    "Windsor",
    "St Kilda",
    "Melbourne",
    "East Melbourne",
    "West Melbourne",
    "South Melbourne",
    "Port Melbourne",
    "Docklands",
    "Cremorne",
    "Clifton Hill",
    "St Kilda West",
]

TARGET = 28


def _venue_uuid(i: int) -> str:
    """Deterministic id 1..28 -> UUID (last segment 12 hex digits)."""
    return f"f1111111-1111-4111-8111-{i:012x}"


def main() -> None:
    rows: list[dict] = []
    with CSV_PATH.open(encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if (row.get("state") or "").strip() not in ("Victoria", "VIC"):
                continue
            c = (row.get("city") or "").strip().lower()
            if c not in ALLOW:
                continue
            try:
                lat = float(row.get("latitude") or 0)
                lon = float(row.get("longitude") or 0)
            except (TypeError, ValueError):
                continue
            if not lat or not lon:
                continue
            gid = (row.get("google_id") or "").strip() or (
                row.get("google_place_url") or ""
            )
            rows.append(
                {
                    "business_name": (row.get("business_name") or "").strip(),
                    "city": (row.get("city") or "").strip(),
                    "street": (row.get("street") or "").strip(),
                    "postal_code": str(row.get("postal_code") or "").replace(".0", ""),
                    "latitude": lat,
                    "longitude": lon,
                    "google_id": gid,
                }
            )

    seen: set = set()
    uniq: list[dict] = []
    for x in rows:
        key = x["google_id"] or (
            x["business_name"].lower(),
            x["city"].lower(),
            x["street"].lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        uniq.append(x)

    by_city: dict[str, list[dict]] = defaultdict(list)
    for u in uniq:
        by_city[u["city"]].append(u)

    # Pass 1: one venue per city in priority order
    selected: list[dict] = []
    for c in PRIORITY:
        if c in by_city and by_city[c]:
            selected.append(by_city[c].pop(0))
        if len(selected) >= TARGET:
            break
    # Pass 2: add second venue per city (breadth) before tripling any city
    if len(selected) < TARGET:
        for c in PRIORITY:
            if c not in by_city or not by_city[c]:
                continue
            selected.append(by_city[c].pop(0))
            if len(selected) >= TARGET:
                break
    # Pass 3: fill remaining, prefer cities with fewest picks so far
    if len(selected) < TARGET:
        count: dict[str, int] = defaultdict(int)
        for u in selected:
            count[u["city"]] += 1
        remaining = [u for u in uniq if u not in selected]
        while len(selected) < TARGET and remaining:
            u = min(
                remaining,
                key=lambda x: (count[x["city"]], x["city"], x["business_name"]),
            )
            remaining.remove(u)
            selected.append(u)
            count[u["city"]] += 1

    lats = [u["latitude"] for u in selected]
    lons = [u["longitude"] for u in selected]
    print("n", len(selected), "distinct cities", len({x["city"] for x in selected}))
    print(
        "bbox lat",
        min(lats),
        max(lats),
        "lon",
        min(lons),
        max(lons),
    )
    for i, u in enumerate(selected, 1):
        print(f"{i:2} {u['city']!s:16} {u['business_name']!s}")

    # Stage 3 role tags (see plan): assign by index 1..28
    def tags_for(i: int) -> list[str]:
        t: list[str] = []
        if 1 <= i <= 3:
            t.append("late_night_crosses_midnight")
        if 4 <= i <= 6:
            t.append("hours_exception")
        if 7 <= i <= 9:
            t.append("sparse_hours_partial_uncertainty")
        if 10 <= i <= 12:
            t.append("meal_special")
        if 13 <= i <= 15:
            t.append("happy_hour")
        if 16 <= i <= 18:
            t.append("drink_special")
        if not t:
            t.append("standard_hours")
        return t

    payload = {
        "source_csv": "dataCollection/Pub_Australia.csv",
        "venue_count": len(selected),
        "suburbs": sorted({u["city"] for u in selected}),
        "selection_note": "Deduplicated by google_id; two-pass city breadth then fill by fewest per city.",
        "venues": [
            {
                "index": i,
                "venue_id": _venue_uuid(i),
                "stage3_roles": tags_for(i),
                **u,
            }
            for i, u in enumerate(selected, 1)
        ],
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    main()
