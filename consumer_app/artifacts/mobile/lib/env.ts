const DEFAULT_API_BASE_URL = "http://localhost:8000";
const DEFAULT_AUTH_REDIRECT_SCHEME = "pubplus";

function readEnv(name: string): string | undefined {
  const value = process.env[name];
  if (!value) return undefined;

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  const configured = readEnv("EXPO_PUBLIC_API_BASE_URL") ?? DEFAULT_API_BASE_URL;
  return normalizeBaseUrl(configured);
}

export function getAuthRedirectScheme(): string {
  return readEnv("EXPO_PUBLIC_AUTH_REDIRECT_SCHEME") ?? DEFAULT_AUTH_REDIRECT_SCHEME;
}

export function getSupabaseUrl(): string | null {
  return readEnv("EXPO_PUBLIC_SUPABASE_URL") ?? null;
}

export function getSupabaseAnonKey(): string | null {
  return readEnv("EXPO_PUBLIC_SUPABASE_ANON_KEY") ?? null;
}

export function hasSupabaseAuthConfig(): boolean {
  return Boolean(getSupabaseUrl() && getSupabaseAnonKey());
}
