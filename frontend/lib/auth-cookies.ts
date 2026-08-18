export const AUTH_COOKIE_NAME = "mbe_token";

// 24h, igual que la duración del JWT que emite el backend (Fase 2). Este es
// el techo duro de la sesión; el cierre por inactividad (IDLE_TIMEOUT_MS,
// más corto) es lo que se dispara primero en el uso normal.
export const AUTH_COOKIE_MAX_AGE = 60 * 60 * 24;

// Minutos sin actividad (mouse, teclado, scroll, touch) tras los cuales se
// cierra la sesión automáticamente. Ver use-idle-logout.ts.
export const IDLE_TIMEOUT_MS = 30 * 60 * 1000;

// No usar NODE_ENV: "production" describe el build de Next.js, no si hay
// TLS delante. Un navegador descarta una cookie Secure servida por HTTP
// plano, así que esto se prende a mano (COOKIE_SECURE=true) recién cuando
// Caddy tenga un dominio real con HTTPS automático.
export const AUTH_COOKIE_SECURE = process.env.COOKIE_SECURE === "true";
