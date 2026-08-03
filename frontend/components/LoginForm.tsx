"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function submitLogin() {
    if (!username || !password || submitting) return;
    setSubmitting(true);
    setLoginError(false);

    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    setSubmitting(false);

    if (!res.ok) {
      setLoginError(true);
      return;
    }

    router.push("/chat");
    router.refresh();
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-surface">
      <div className="w-[400px] bg-surface border border-border rounded-2xl p-10 flex flex-col items-center gap-[22px]">
        <div className="w-12 h-12 rounded-[10px] bg-navy text-surface flex items-center justify-center text-[11px] font-semibold font-mono">
          PUJ
        </div>
        <div className="text-center">
          <div className="text-xl font-semibold text-ink">Asistente MBE</div>
          <div className="text-[13px] text-ink-soft mt-1">
            Facultad de Medicina — Pontificia Universidad Javeriana
          </div>
        </div>

        <div className="w-full flex flex-col gap-3.5">
          <label className="flex flex-col gap-1.5 text-[13px] text-ink-soft">
            Usuario
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="usuario@javeriana.edu.co"
              className="border border-border rounded-[9px] px-[13px] py-[11px] text-sm font-sans text-ink bg-surface outline-none"
            />
          </label>
          <label className="flex flex-col gap-1.5 text-[13px] text-ink-soft">
            Contraseña
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submitLogin();
              }}
              placeholder="••••••••"
              className="border border-border rounded-[9px] px-[13px] py-[11px] text-sm font-sans text-ink bg-surface outline-none"
            />
          </label>

          {loginError && (
            <div className="text-[13px] text-danger">
              Usuario o contraseña incorrectos.
            </div>
          )}

          <button
            onClick={submitLogin}
            disabled={submitting}
            className="mt-1 p-3 bg-navy text-surface border-none rounded-[9px] text-sm font-semibold cursor-pointer disabled:opacity-60"
          >
            {submitting ? "Ingresando…" : "Iniciar sesión"}
          </button>
        </div>
      </div>
    </div>
  );
}
