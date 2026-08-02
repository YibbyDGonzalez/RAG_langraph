import { authHeader, fastapiUrl } from "@/lib/fastapi";

export async function GET() {
  const auth = await authHeader();
  if (!auth) {
    return Response.json({ detail: "No autenticado" }, { status: 401 });
  }

  const res = await fetch(fastapiUrl("/api/conversations"), {
    headers: auth,
    cache: "no-store",
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}

export async function POST() {
  const auth = await authHeader();
  if (!auth) {
    return Response.json({ detail: "No autenticado" }, { status: 401 });
  }

  const res = await fetch(fastapiUrl("/api/conversations"), {
    method: "POST",
    headers: auth,
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
