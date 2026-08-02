import { authHeader, fastapiUrl } from "@/lib/fastapi";

export async function POST(request: Request) {
  const auth = await authHeader();
  if (!auth) {
    return Response.json({ detail: "No autenticado" }, { status: 401 });
  }

  const body = await request.text();

  const fastapiRes = await fetch(fastapiUrl("/api/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...auth },
    body,
  });

  if (!fastapiRes.ok || !fastapiRes.body) {
    const detail = await fastapiRes.text().catch(() => "");
    return new Response(detail || "Error del backend", { status: fastapiRes.status });
  }

  // Pasa el stream SSE de FastAPI tal cual, sin bufferear.
  return new Response(fastapiRes.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
