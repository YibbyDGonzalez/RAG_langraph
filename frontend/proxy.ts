import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth-cookies";

// Chequeo optimista (sin verificar firma/expiración del JWT): si no hay
// cookie, ni vale la pena llegar a /chat. La validación real ocurre en
// cada request server-side contra FastAPI (que rechaza con 401 si el
// token es inválido o expiró), y esas páginas redirigen a /login también.
export function proxy(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
}

export const config = {
  matcher: ["/chat/:path*", "/reporte/:path*"],
};
