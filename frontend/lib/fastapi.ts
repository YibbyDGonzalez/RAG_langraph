import { cookies } from "next/headers";

import { AUTH_COOKIE_NAME } from "@/lib/auth-cookies";

const FASTAPI_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function fastapiUrl(path: string): string {
  return `${FASTAPI_URL}${path}`;
}

/** Lee el JWT de la cookie httpOnly. Solo se puede llamar server-side
 * (Server Components, Route Handlers) — el cliente nunca ve el token. */
export async function getToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(AUTH_COOKIE_NAME)?.value ?? null;
}

/** Header Authorization listo para reenviar a FastAPI, o null si no hay sesión. */
export async function authHeader(): Promise<{ Authorization: string } | null> {
  const token = await getToken();
  if (!token) return null;
  return { Authorization: `Bearer ${token}` };
}
