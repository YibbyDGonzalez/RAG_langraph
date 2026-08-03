import { redirect } from "next/navigation";

import { ChatShell } from "@/components/ChatShell";
import { authHeader, fastapiUrl } from "@/lib/fastapi";
import type { ConversationSummary } from "@/lib/types";

export default async function ChatPage() {
  const auth = await authHeader();
  if (!auth) redirect("/login");

  const meRes = await fetch(fastapiUrl("/api/auth/me"), { headers: auth, cache: "no-store" });
  if (!meRes.ok) redirect("/login");
  const me: { user_id: string; role: string } = await meRes.json();

  const conversationsRes = await fetch(fastapiUrl("/api/conversations"), {
    headers: auth,
    cache: "no-store",
  });
  const conversations: ConversationSummary[] = conversationsRes.ok
    ? await conversationsRes.json()
    : [];

  return <ChatShell userName={me.user_id} role={me.role} initialConversations={conversations} />;
}
