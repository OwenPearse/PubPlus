import { getAccessToken } from "@/lib/supabase";
import { getApiBaseUrl } from "@/lib/env";

export type ApiRequestOptions = RequestInit & {
  query?: Record<string, string | number | boolean | null | undefined>;
  requireAuth?: boolean;
};

export type ApiErrorCode =
  | "network_error"
  | "validation_error"
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "server_error"
  | "unknown_error";

export type ApiRequestError = {
  code: ApiErrorCode;
  message: string;
  status: number | null;
  details?: unknown;
  isAuthRequired?: boolean;
};

const DEFAULT_HEADERS: HeadersInit = {
  Accept: "application/json, application/problem+json",
};

const apiBaseUrl = getApiBaseUrl();

function isHttpMethodWithBody(method?: string): boolean {
  const normalized = method?.toUpperCase();
  return normalized === "POST" || normalized === "PUT" || normalized === "PATCH" || normalized === "DELETE";
}

function toApiPath(path: string): string {
  if (!path) return "/api/v1/health";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${apiBaseUrl}${normalizedPath}`;
}

function applyQuery(path: string, query?: ApiRequestOptions["query"]): string {
  if (!query || Object.keys(query).length === 0) return path;

  const queryString = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value == null) continue;
    queryString.set(key, String(value));
  }

  const encoded = queryString.toString();
  if (!encoded) return path;
  return path.includes("?") ? `${path}&${encoded}` : `${path}?${encoded}`;
}

function buildHeaders(optionsHeaders?: HeadersInit, body?: BodyInit | null, method?: string): Headers {
  const headers = new Headers(DEFAULT_HEADERS);

  if (optionsHeaders) {
    const customHeaders = new Headers(optionsHeaders);
    customHeaders.forEach((value, key) => headers.set(key, value));
  }

  if (typeof body === "string" && isHttpMethodWithBody(method) && !headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }

  return headers;
}

function toApiRequestError(error: unknown): ApiRequestError {
  if (error && typeof error === "object" && "status" in error) {
    const status = Number((error as { status?: number }).status);
    const message =
      error instanceof Error ? error.message : `Request failed with HTTP status ${status}`;
    const details = (error as { data?: unknown }).data;
    if (status === 400 || status === 422) {
      return {
        code: "validation_error",
        message,
        status,
        details,
      };
    }

    if (status === 401) {
      return {
        code: "unauthorized",
        message,
        status,
        details,
        isAuthRequired: true,
      };
    }

    if (status === 403) {
      return {
        code: "forbidden",
        message,
        status,
        details,
      };
    }

    if (status === 404) {
      return {
        code: "not_found",
        message,
        status,
        details,
      };
    }

    if (status >= 500) {
      return {
        code: "server_error",
        message,
        status,
        details,
      };
    }

    return {
      code: "unknown_error",
      message,
      status,
      details,
    };
  }

  if (error instanceof TypeError) {
    return {
      code: "network_error",
      message: error.message,
      status: null,
      details: error,
    };
  }

  return {
    code: "unknown_error",
    message: error instanceof Error ? error.message : "Unknown request failure",
    status: null,
    details: error,
  };
}

function normalizeBody(body: unknown): BodyInit | null | undefined {
  if (body == null) return body as null | undefined;
  if (typeof body === "string" || body instanceof FormData || body instanceof URLSearchParams) {
    return body;
  }
  return JSON.stringify(body);
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { query, requireAuth, headers: headersInit, body, method, ...rest } = options;

  const url = applyQuery(toApiPath(path), query);
  const normalizedBody = normalizeBody(body);
  const headers = buildHeaders(headersInit, normalizedBody ?? null, method);
  if (requireAuth && !headers.has("authorization")) {
    const token = await getAccessToken();
    if (!token) {
      throw {
        code: "unauthorized",
        message: "Authentication is required for this request.",
        status: 401,
        isAuthRequired: true,
      } as ApiRequestError;
    }
    headers.set("authorization", `Bearer ${token}`);
  }

  try {
    const response = await fetch(url, {
      ...rest,
      method: method ?? "GET",
      body: normalizedBody,
      headers,
    });

    if (!response.ok) {
      const payloadText = await response.text();
      let payload: unknown = null;
      if (payloadText) {
        try {
          payload = JSON.parse(payloadText);
        } catch {
          payload = payloadText;
        }
      }

      throw {
        status: response.status,
        data: payload,
        message: `HTTP ${response.status} ${response.statusText}`,
      };
    }

    if (response.status === 204 || response.status === 205) {
      return null as T;
    }

    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      return (await response.json()) as T;
    }

    return (await response.text()) as T;
  } catch (error) {
    throw toApiRequestError(error);
  }
}

export function publicApiRequest<T>(path: string, options: Omit<ApiRequestOptions, "requireAuth"> = {}) {
  return apiRequest<T>(path, { ...options, requireAuth: false });
}

export function privateApiRequest<T>(path: string, options: Omit<ApiRequestOptions, "requireAuth"> = {}) {
  return apiRequest<T>(path, { ...options, requireAuth: true });
}

export async function healthCheck() {
  return publicApiRequest<{ status: string }>("/api/v1/health");
}

export { apiBaseUrl };
