"""Truncated notes for list/export DTOs (no full raw notes)."""

NOTES_SUMMARY_MAX_LEN = 200


def truncate_notes_summary(notes: str | None, *, max_len: int = NOTES_SUMMARY_MAX_LEN) -> str:
    if not notes:
        return ""
    collapsed = " ".join(str(notes).split())
    if len(collapsed) <= max_len:
        return collapsed
    return collapsed[: max_len - 3] + "..."
