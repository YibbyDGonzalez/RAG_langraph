import { authHeader, fastapiUrl } from "@/lib/fastapi";

export async function POST(request: Request) {
  const auth = await authHeader();
  if (!auth) {
    return Response.json({ detail: "No autenticado" }, { status: 401 });
  }

  const { search } = new URL(request.url);

  const res = await fetch(fastapiUrl(`/api/report/temas/generate${search}`), {
    method: "POST",
    headers: auth,
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
