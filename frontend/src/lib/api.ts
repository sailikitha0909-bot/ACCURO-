const API_BASE = "/api/v1";

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("accuro_token");
  }
  return null;
}

export function getCurrentUser(): any {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem("accuro_user");
    return raw ? JSON.parse(raw) : null;
  }
  return null;
}

export function setAuthSession(token: string, user: any) {
  if (typeof window !== "undefined") {
    localStorage.setItem("accuro_token", token);
    localStorage.setItem("accuro_user", JSON.stringify(user));
  }
}

export function clearAuthSession() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("accuro_token");
    localStorage.removeItem("accuro_user");
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Set json content type unless sending FormData
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearAuthSession();
    if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = await res.text();
    }
    throw new Error(errorDetail);
  }

  // Handle binary / non-json responses (e.g. downloads)
  const contentType = res.headers.get("content-type");
  if (contentType && (contentType.includes("application/xml") || contentType.includes("application/pdf") || contentType.includes("spreadsheetml"))) {
    return (await res.blob()) as unknown as T;
  }

  return res.json();
}
