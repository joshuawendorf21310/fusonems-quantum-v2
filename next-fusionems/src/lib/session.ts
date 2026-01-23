const SESSION_TOKEN_KEY = "fusonems.session.token";
const apiBase =
  import.meta.env.VITE_API_URL ??
  (import.meta.env as { NEXT_PUBLIC_API_URL?: string }).NEXT_PUBLIC_API_URL ??
  "";

export function setSessionToken(token: string): void {
  localStorage.setItem(SESSION_TOKEN_KEY, token);
}

export function clearSessionToken(): void {
  localStorage.removeItem(SESSION_TOKEN_KEY);
}

export function getSessionToken(): string | null {
  return localStorage.getItem(SESSION_TOKEN_KEY);
}

export async function getSession(): Promise<{
  id: string;
  orgId: string;
  email: string;
  role: string;
} | null> {
  const token = getSessionToken();
  if (!token) {
    return null;
  }
  const response = await fetch(`${apiBase}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    return null;
  }
  return response.json();
}
