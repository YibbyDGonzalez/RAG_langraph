import { cookies } from "next/headers";

import { AUTH_COOKIE_MAX_AGE, AUTH_COOKIE_NAME, AUTH_COOKIE_SECURE } from "@/lib/auth-cookies";
import { fastapiUrl } from "@/lib/fastapi";

export async function POST(request: Request) {
  const body = await request.json();

  const fastapiRes = await fetch(fastapiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!fastapiRes.ok) {
    const detail = await fastapiRes.json().catch(() => ({}));
    return Response.json(
      { detail: detail.detail ?? "No se pudo iniciar sesión" },
      { status: fastapiRes.status },
    );
  }

  const data = await fastapiRes.json();

  const cookieStore = await cookies();
  cookieStore.set(AUTH_COOKIE_NAME, data.access_token, {
    httpOnly: true,
    secure: AUTH_COOKIE_SECURE,
    sameSite: "lax",
    path: "/",
    maxAge: AUTH_COOKIE_MAX_AGE,
  });

  return Response.json({ role: data.role });
}
