/** Normalize Search `q` to match backend `normalize_discovery_q` semantics. */
export function normalizeSearchQ(raw: string): string | undefined {
  const trimmed = raw.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}
