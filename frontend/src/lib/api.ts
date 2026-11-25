/**
 * Central API Client for AI Investment Advisor
 * Communicates with FastAPI backend on http://127.0.0.1:8000
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("advisor_token");
}

export function setAuthToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem("advisor_token", token);
  } else {
    localStorage.removeItem("advisor_token");
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      if (typeof errorJson.detail === "string") {
        errorDetail = errorJson.detail;
      } else if (Array.isArray(errorJson.detail)) {
        errorDetail = errorJson.detail.map((e: any) => e.msg || e).join(", ");
      } else if (errorJson.message) {
        errorDetail = errorJson.message;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

