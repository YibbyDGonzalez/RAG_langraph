import { cookies } from "next/headers";

import { AUTH_COOKIE_NAME } from "@/lib/auth-cookies";

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete(AUTH_COOKIE_NAME);
  return new Response(null, { status: 204 });
}
