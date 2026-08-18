"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { ChatInput } from "@/components/ChatInput";
import { MessageBubble } from "@/components/MessageBubble";
import { Sidebar } from "@/components/Sidebar";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { useIdleLogout } from "@/lib/use-idle-logout";
import type { ConversationSummary, Message } from "@/lib/types";

interface ChatShellProps {
  userName: string;
  role: string;
  initialConversations: ConversationSummary[];
}

export function ChatShell({ userName, role, initialConversations }: ChatShellProps) {
  const router = useRouter();
  useIdleLogout();
  const [conversations, setConversations] = useState(initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Al entrar: retoma la conversación más reciente, o crea una nueva si no hay historial.
    if (initialConversations.length > 0) {
      void selectConversation(initialConversations[0].id);
    } else {
      void startNewConversation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  async function startNewConversation() {
    const res = await fetch("/api/conversations", { method: "POST" });
    const data = await res.json();
    setActiveConversationId(data.id);
    setMessages([]);
    setDraft("");
    setIsGenerating(false);
  }

  async function selectConversation(id: string) {
    setActiveConversationId(id);
    setDraft("");
    setIsGenerating(false);
    const res = await fetch(`/api/conversations/${id}`);
    setMessages(res.ok ? (await res.json()).messages : []);
  }

  async function refreshConversations() {
    const res = await fetch("/api/conversations");
    if (res.ok) setConversations(await res.json());
  }

  async function send(text?: string) {
    const pregunta = (text ?? draft).trim();
    if (!pregunta || isGenerating || !activeConversationId) return;

    const isFirstMessage = messages.length === 0;

    setDraft("");
    setIsGenerating(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: pregunta },
      { role: "assistant", content: "" },
    ]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: activeConversationId, pregunta }),
        signal: controller.signal,
      });

      if (res.status === 401) {
        router.push("/login");
        return;
      }
      if (!res.ok || !res.body) {
        throw new Error("chat request failed");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const rawEvents = buffer.split("\n\n");
        buffer = rawEvents.pop() ?? "";

        for (const rawEvent of rawEvents) {
          const dataLine = rawEvent.split("\n").find((line) => line.startsWith("data: "));
          if (!dataLine) continue;
          const payload = JSON.parse(dataLine.slice("data: ".length));
          if (typeof payload.token === "string") {
            appendToLastMessage(payload.token);
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = {
            role: "assistant",
            content: "Ocurrió un error al generar la respuesta. Intenta de nuevo.",
          };
          return next;
        });
      }
    } finally {
      setIsGenerating(false);
      abortRef.current = null;
      if (isFirstMessage) void refreshConversations();
    }
  }

  function appendToLastMessage(token: string) {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      next[next.length - 1] = { ...last, content: last.content + token };
      return next;
    });
  }

  function stop() {
    abortRef.current?.abort();
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  const isStreamingLast = isGenerating && messages[messages.length - 1]?.role === "assistant";

  return (
    <div className="flex h-screen w-full text-ink bg-surface">
      <Sidebar
        userName={userName}
        role={role}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={(id) => void selectConversation(id)}
        onNewConversation={() => void startNewConversation()}
        onLogout={() => void logout()}
      />
      <main className="flex-1 flex flex-col h-screen">
        {messages.length === 0 ? (
          <WelcomeScreen userName={userName} onSelectSuggestion={(text) => void send(text)} />
        ) : (
          <div ref={containerRef} className="flex-1 overflow-y-auto px-10 py-8">
            <div className="max-w-[720px] mx-auto w-full flex flex-col gap-[18px]">
              {messages.map((m, i) => (
                <MessageBubble
                  key={i}
                  role={m.role}
                  content={m.content}
                  streaming={isStreamingLast && i === messages.length - 1}
                />
              ))}
            </div>
          </div>
        )}
        <ChatInput
          draft={draft}
          onDraftChange={setDraft}
          onSend={() => void send()}
          onStop={stop}
          isGenerating={isGenerating}
        />
      </main>
    </div>
  );
}
