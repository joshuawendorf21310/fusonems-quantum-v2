const apiBase =
  import.meta.env.VITE_API_URL ??
  (import.meta.env as { NEXT_PUBLIC_API_URL?: string }).NEXT_PUBLIC_API_URL ??
  "";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Request failed");
  }
  return response.json() as Promise<T>;
}
