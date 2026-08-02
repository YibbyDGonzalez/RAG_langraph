import { authHeader, fastapiUrl } from "@/lib/fastapi";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const auth = await authHeader();
  if (!auth) {
    return Response.json({ detail: "No autenticado" }, { status: 401 });
  }

  const { id } = await params;
  const res = await fetch(fastapiUrl(`/api/conversations/${id}`), {
    headers: auth,
    cache: "no-store",
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
