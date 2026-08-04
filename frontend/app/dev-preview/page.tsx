"use client";

import { Suspense } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ReportSidebar } from "@/components/report/ReportSidebar";

export default function DevPreviewPage() {
  return (
    <div className="flex h-screen w-full">
      <Sidebar
        userName="Sebastian Ruiz"
        role="Docente"
        conversations={[
          { id: "1", title: "Conversación de ejemplo" },
          { id: "2", title: "Otra conversación" },
        ]}
        activeConversationId="1"
        onSelectConversation={() => {}}
        onNewConversation={() => {}}
        onLogout={() => {}}
      />
      <Suspense fallback={null}>
        <ReportSidebar teacherName="Juan Pajaro" minDate="2026-01-01" maxDate="2026-08-03" />
      </Suspense>
    </div>
  );
}
