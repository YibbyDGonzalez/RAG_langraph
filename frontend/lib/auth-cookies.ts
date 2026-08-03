export const AUTH_COOKIE_NAME = "mbe_token";

// 24h, igual que la duración del JWT que emite el backend (Fase 2).
export const AUTH_COOKIE_MAX_AGE = 60 * 60 * 24;

// No usar NODE_ENV: "production" describe el build de Next.js, no si hay
// TLS delante. Un navegador descarta una cookie Secure servida por HTTP
// plano, así que esto se prende a mano (COOKIE_SECURE=true) recién cuando
// Caddy tenga un dominio real con HTTPS automático.
export const AUTH_COOKIE_SECURE = process.env.COOKIE_SECURE === "true";
