"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { IDLE_TIMEOUT_MS } from "@/lib/auth-cookies";

const CHECK_INTERVAL_MS = 30 * 1000;
const ACTIVITY_THROTTLE_MS = 5 * 1000;
const LAST_ACTIVITY_KEY = "mbe_last_activity";
const ACTIVITY_EVENTS = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"] as const;

/**
 * Cierra la sesión (borra la cookie del JWT y redirige a /login) si el
 * usuario no interactúa con la página por IDLE_TIMEOUT_MS. El último
 * timestamp de actividad se guarda en localStorage (compartido entre
 * pestañas del mismo origen) para que actividad en una pestaña no deje que
 * otra pestaña inactiva se cierre de forma inconsistente.
 */
export function useIdleLogout() {
  const router = useRouter();

  useEffect(() => {
    let lastMarked = 0;

    function markActivity() {
      const now = Date.now();
      if (now - lastMarked < ACTIVITY_THROTTLE_MS) return;
      lastMarked = now;
      localStorage.setItem(LAST_ACTIVITY_KEY, String(now));
    }

    async function logout() {
      await fetch("/api/auth/logout", { method: "POST" });
      router.push("/login");
      router.refresh();
    }

    function checkIdle() {
      const raw = localStorage.getItem(LAST_ACTIVITY_KEY);
      const last = raw ? Number(raw) : Date.now();
      if (Date.now() - last >= IDLE_TIMEOUT_MS) void logout();
    }

    markActivity();
    for (const evento of ACTIVITY_EVENTS) {
      window.addEventListener(evento, markActivity, { passive: true });
    }
    const interval = setInterval(checkIdle, CHECK_INTERVAL_MS);

    return () => {
      for (const evento of ACTIVITY_EVENTS) {
        window.removeEventListener(evento, markActivity);
      }
      clearInterval(interval);
    };
  }, [router]);
}
