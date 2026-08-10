"use client";

import Image from "next/image";
import Link from "next/link";

import { TeamCredits } from "@/components/TeamCredits";
import type { ConversationSummary } from "@/lib/types";

interface SidebarProps {
  userName: string;
  role: string;
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onLogout: () => void;
}

export function Sidebar({
  userName,
  role,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onLogout,
}: SidebarProps) {
  return (
    <aside className="w-[280px] min-w-[280px] bg-surface-alt border-r border-border flex flex-col p-[22px_18px] gap-5">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-surface border border-border flex items-center justify-center p-1 flex-shrink-0">
          <Image src="/javeriana-crest.png" alt="Javeriana" width={28} height={28} className="w-full h-full object-contain" />
        </div>
        <div className="text-sm font-semibold">Asistente MBE</div>
      </div>

      <button
        onClick={onNewConversation}
        className="flex items-center justify-center gap-2 p-[11px] bg-surface-selected text-navy border border-border rounded-[9px] text-sm font-semibold cursor-pointer"
      >
        + Nueva conversación
      </button>

      <div className="flex flex-col gap-2 flex-1 overflow-y-auto">
        <div className="text-[11px] font-semibold tracking-[0.04em] uppercase text-ink-muted px-1">
          Conversaciones
        </div>
        {conversations.length === 0 ? (
          <div className="text-[13px] text-ink-muted px-1 py-2 leading-relaxed">
            Aún no tienes conversaciones anteriores.
          </div>
        ) : (
          conversations.map((c) => {
            const active = c.id === activeConversationId;
            return (
              <button
                key={c.id}
                onClick={() => onSelectConversation(c.id)}
                className={`text-left px-3 py-2.5 rounded-[9px] text-[13px] whitespace-nowrap overflow-hidden text-ellipsis cursor-pointer border-0 border-l-[3px] text-ink ${
                  active
                    ? "border-l-teal bg-surface-selected"
                    : "border-l-transparent bg-transparent"
                }`}
              >
                {c.title}
              </button>
            );
          })
        )}
      </div>

      {role === "Docente" && (
        <Link
          href="/reporte"
          className="flex items-center gap-2 px-3 py-2.5 rounded-[9px] text-[13px] font-semibold text-navy bg-surface-selected border border-border"
        >
          📊 Reporte de uso
        </Link>
      )}

      <div className="flex flex-col gap-1 pt-3 px-1 border-t border-border">
        <div className="text-[13px] font-semibold">{userName}</div>
        <button
          onClick={onLogout}
          className="self-start bg-transparent border-none p-0 text-[13px] text-ink-soft cursor-pointer"
        >
          Cerrar sesión
        </button>
      </div>

      <div className="px-1">
        <TeamCredits />
      </div>
    </aside>
  );
}
