/**
 * Product analytics + Telegram-native sharing/referral helpers.
 *
 * - track(event, props): fire-and-forget event to the backend funnel.
 * - shareInvite(): opens Telegram share with the user's referral deep-link.
 * - getStartParam(): reads the referral param from the launch (for attribution).
 *
 * All functions are defensive: they never throw and never block the UI.
 */

import WebApp from "@twa-dev/sdk";
import { t } from "./i18n";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const BOT_USERNAME = "vetai_app_bot";
const MINIAPP_URL = "https://andrew32bit.github.io/vetai/";

// One session id per app launch — lets us measure sessions & session length.
function makeSessionId() {
  return `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}
let SESSION_ID = null;
export function getSessionId() {
  if (!SESSION_ID) SESSION_ID = makeSessionId();
  return SESSION_ID;
}

export function getTelegramId() {
  return localStorage.getItem("vetai_telegram_id") || null;
}

/** Referral param passed at launch, e.g. "ref_12345" → returns raw string or null. */
export function getStartParam() {
  try {
    return WebApp.initDataUnsafe?.start_param || null;
  } catch {
    return null;
  }
}

/** Parse a referrer telegram_id from the launch start_param. */
export function getReferrerId() {
  const sp = getStartParam();
  if (!sp) return null;
  const m = String(sp).match(/^ref_?(\d+)$/i);
  return m ? Number(m[1]) : null;
}

/**
 * Fire-and-forget analytics event. Uses keepalive so it survives page unload.
 */
export function track(event, props = {}) {
  try {
    fetch(`${API_URL}/api/v1/analytics/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      keepalive: true,
      body: JSON.stringify({
        event,
        telegram_id: getTelegramId() ? Number(getTelegramId()) : null,
        session_id: getSessionId(),
        props,
      }),
    }).catch(() => {});
  } catch {
    // never let analytics break the app
  }
}

/** The user's personal invite link (opens the Mini App with their ref param). */
export function inviteLink() {
  const tid = getTelegramId();
  if (tid) return `https://t.me/${BOT_USERNAME}?startapp=ref_${tid}`;
  return `https://t.me/${BOT_USERNAME}`;
}

/**
 * Open Telegram's native share sheet with the referral link.
 * Falls back to clipboard/new-tab outside Telegram (dev).
 */
export function shareInvite(text) {
  const link = inviteLink();
  const shareText = text || t("inviteShareText");
  const url = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(shareText)}`;
  track("invite_click");
  try {
    WebApp.openTelegramLink(url);
    return;
  } catch {
    // fall through
  }
  try {
    if (navigator.share) {
      navigator.share({ text: `${shareText} ${link}` });
      return;
    }
  } catch {}
  try {
    navigator.clipboard?.writeText(`${shareText} ${link}`);
  } catch {}
  try {
    window.open(url, "_blank");
  } catch {}
}

/**
 * Share a diagnosis/chat result outward (invite + short result summary).
 */
export function shareResult(summary) {
  const link = inviteLink();
  const suffix = t("shareResultSuffix");
  const text = summary ? `${summary}\n\n${suffix}` : suffix;
  const url = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;
  track("share_result_click");
  try {
    WebApp.openTelegramLink(url);
    return;
  } catch {}
  try {
    if (navigator.share) { navigator.share({ text: `${text} ${link}` }); return; }
  } catch {}
  try { navigator.clipboard?.writeText(`${text} ${link}`); } catch {}
}
