const DEFAULT_API_BASE_URL = "http://localhost:8000";

function readEnv(name: string): string | undefined {
  const value = import.meta.env[name];
  if (!value || typeof value !== "string") return undefined;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function getApiBaseUrl(): string {
  const configured = readEnv("VITE_API_BASE_URL") ?? DEFAULT_API_BASE_URL;
  return configured.replace(/\/+$/, "");
}

export function getSupabaseUrl(): string | null {
  return readEnv("VITE_SUPABASE_URL") ?? null;
}

/** Supabase publishable (anon) key — `sb_publishable_…` or legacy anon JWT. */
export function getSupabasePublishableKey(): string | null {
  return (
    readEnv("VITE_SUPABASE_PUBLISHABLE_KEY") ??
    readEnv("VITE_SUPABASE_ANON_KEY") ??
    null
  );
}

export function hasSupabaseAuthConfig(): boolean {
  return Boolean(getSupabaseUrl() && getSupabasePublishableKey());
}

export function getPortalSupportUrl(): string | null {
  return readEnv("VITE_PORTAL_SUPPORT_URL") ?? null;
}
