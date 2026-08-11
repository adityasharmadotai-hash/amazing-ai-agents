/**
 * index.js — unofficial QR-linked WhatsApp bot (Baileys).
 *
 *  ⚠️  This uses WhatsApp's WEB/linked-device protocol via an unofficial library.
 *      It VIOLATES WhatsApp's Terms of Service and the linked number can be
 *      PERMANENTLY BANNED. Test on a SPARE number, never your main line first.
 *
 * What it does:
 *   1. Prints a QR code — scan it from WhatsApp → Linked devices (like WhatsApp Web).
 *   2. On each incoming DM, POSTs the text to the local Python agent server
 *      (agent_server.py, http://127.0.0.1:8100/reply), which runs the FutrBridge
 *      Gemini brain and returns a reply.
 *   3. Sends that reply back over WhatsApp. If the agent escalates, it also pings
 *      the team number(s) from TEAM_WHATSAPP_NUMBERS.
 *
 * Run:
 *   1) In the project root:  python agent_server.py
 *   2) Here:                 npm install  &&  npm start
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
// Load the shared project .env (one level up) so the bot and the Python agent
// read the same config (TEAM_GROUP_NAME, ALERT_WEBHOOK_URL, AGENT_URL, …).
dotenv.config({ path: path.join(path.dirname(fileURLToPath(import.meta.url)), "..", ".env") });

import { Boom } from "@hapi/boom";
import makeWASocket, {
  DisconnectReason,
  downloadMediaMessage,
  fetchLatestBaileysVersion,
  useMultiFileAuthState,
} from "@whiskeysockets/baileys";
import pino from "pino";
import QRImage from "qrcode";
import qrcode from "qrcode-terminal";

const AGENT_URL = process.env.AGENT_URL || "http://127.0.0.1:8100";
const AUTH_DIR = process.env.AUTH_DIR || "auth";
// Escalations are posted to this WhatsApp group (the bot's number must be a member).
const TEAM_GROUP_NAME = process.env.TEAM_GROUP_NAME || "AX Reply";
let teamGroupJid = null;

// External alert channels for events WhatsApp can't deliver (e.g. the bot logging
// out). Configure a Telegram group (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID) and/or
// a generic Discord/Slack/custom webhook (ALERT_WEBHOOK_URL).
const ALERT_WEBHOOK_URL = process.env.ALERT_WEBHOOK_URL || "";
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || "";

async function notifyAlert(text) {
  console.log("🔔 ALERT: " + text);
  const sends = [];
  if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
    sends.push(
      fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: TELEGRAM_CHAT_ID, text }),
      }),
    );
  }
  if (ALERT_WEBHOOK_URL) {
    sends.push(
      fetch(ALERT_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // `content` works for Discord, `text` for Slack; custom endpoints get both.
        body: JSON.stringify({ content: text, text }),
      }),
    );
  }
  for (const s of sends) {
    try { await s; } catch (e) { console.log("alert send failed: " + e.message); }
  }
}

const logger = pino({ level: "silent" });
let teamNumbers = new Set();
let reconnecting = false;
let currentSock = null;

// Debounce: people send several short messages in a burst. Collect them per
// chat and answer ONCE when they pause, instead of replying to each fragment.
const pending = new Map(); // jid -> { parts: [], timer, name, phone }
const DEBOUNCE_MS = 3000;

// waId -> the real chat jid we last received from, so a group command can relay
// a message back to that exact candidate (handles @lid vs @s.whatsapp.net).
const jidByWaId = new Map();

// Store of messages we've seen/sent (id -> full message). Baileys' getMessage()
// uses this to RE-SEND a message with a fresh session when the recipient couldn't
// decrypt it (a "retry receipt"). Without it, undecryptable messages get stuck on
// "Waiting for this message…" forever. This is the fix for that.
const msgStore = new Map();
function rememberMessage(m) {
  if (!m?.key?.id) return;
  msgStore.set(m.key.id, m);
  if (msgStore.size > 1500) msgStore.delete(msgStore.keys().next().value);
}

// Sent-alert message id -> { waId, name }. Lets the team just REPLY to an alert
// in the group and have the bot relay to that exact candidate (no name needed).
const alertRefByMsgId = new Map();
function rememberAlert(id, ref) {
  if (!id) return;
  alertRefByMsgId.set(id, ref);
  if (alertRefByMsgId.size > 500) alertRefByMsgId.delete(alertRefByMsgId.keys().next().value);
}

// Last-resort guards: log and keep running instead of crashing the whole bot.
process.on("unhandledRejection", (e) =>
  console.log("⚠️  unhandledRejection:", e?.message || e),
);
process.on("uncaughtException", (e) =>
  console.log("⚠️  uncaughtException:", e?.message || e),
);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Feel human: pause to "read", then "type" for a bit before sending. Scales with
// reply length, capped, with a little randomness so it's never metronomic.
function replyDelayMs(text) {
  const base = 1800 + (text?.length || 0) * 45; // ~reading + typing speed
  return Math.min(base, 9000) + Math.floor(Math.random() * 900);
}

// Send that never throws — a dropped connection must never crash the bot.
async function safeSend(sock, jid, text) {
  try {
    await sock.sendMessage(jid, { text });
    return true;
  } catch (e) {
    console.log(`   (send to ${jid} failed: ${e.message})`);
    return false;
  }
}

// Pull the team numbers (to skip auto-replying to teammates) from the agent server.
async function loadTeamNumbers() {
  try {
    const res = await fetch(`${AGENT_URL}/health`);
    const data = await res.json();
    teamNumbers = new Set((data.team_numbers || []).map(String));
    console.log(
      `🧠 Agent server OK — business: ${data.business}, Gemini: ${data.gemini_configured ? "on" : "OFF"}`,
    );
  } catch (e) {
    console.log(`⚠️  Could not reach agent server at ${AGENT_URL} — is agent_server.py running?`);
  }
}

// Ask the Python brain for a reply.
async function askAgent(waId, text, name, phone) {
  const res = await fetch(`${AGENT_URL}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wa_id: waId, text, name, phone: phone || undefined }),
  });
  if (!res.ok) throw new Error(`agent server ${res.status}`);
  return res.json();
}

function extractText(msg) {
  const m = msg.message || {};
  return (
    m.conversation ||
    m.extendedTextMessage?.text ||
    m.imageMessage?.caption ||
    m.videoMessage?.caption ||
    ""
  );
}

// How many times a message has been forwarded. WhatsApp flags "forwarded many
// times" at score >= 4 — that's almost always chain-spam, never a real candidate.
function forwardScore(msg) {
  const m = msg.message || {};
  const ci =
    m.extendedTextMessage?.contextInfo ||
    m.imageMessage?.contextInfo ||
    m.videoMessage?.contextInfo ||
    m.documentMessage?.contextInfo ||
    {};
  return ci.forwardingScore || 0;
}

// When a chat is LID-based (remoteJid ends in @lid), the sender's real phone
// number is exposed as an "alt" on the key. Return it as +<digits>, or "".
function phoneFromKey(msg) {
  const alt =
    msg.key?.remoteJidAlt || msg.key?.senderPn || msg.key?.participantAlt || "";
  const mm = String(alt).match(/(\d{6,15})@s\.whatsapp\.net/);
  return mm ? "+" + mm[1] : "";
}

// Send a voice note's audio to the agent server for Gemini transcription.
async function transcribeAudio(b64, mime) {
  const res = await fetch(`${AGENT_URL}/transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audio_b64: b64, mime }),
  });
  if (!res.ok) throw new Error(`transcribe ${res.status}`);
  const data = await res.json();
  return (data.text || "").trim();
}

// Best-effort jid for a candidate we don't have a live chat handle for.
function candidateJid(waId) {
  const digits = String(waId).replace(/\D/g, "");
  return digits.length >= 15 ? `${digits}@lid` : `${digits}@s.whatsapp.net`;
}

// A teammate wrote "Ax, …" in the team group. Ask the brain who they mean and
// what to say, relay it to that candidate, and confirm back in the group.
async function handleGroupCommand(sock, msg, text, ref) {
  // Replying to an alert → the whole text is the instruction; otherwise strip "Ax".
  const command = ref ? text.trim() : text.replace(/^\s*@?ax\b[,:]?\s*/i, "").trim();
  if (!command) return;
  console.log(`🛠️  group command from ${msg.pushName || "team"}${ref ? ` (re: ${ref.name})` : ""}: ${command}`);
  try {
    const body = { text: command };
    if (ref) { body.target_wa_id = ref.waId; body.target_name = ref.name; }
    const res = await fetch(`${AGENT_URL}/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const out = await res.json();
    if (out.found && out.wa_id && out.message) {
      const target = jidByWaId.get(String(out.wa_id)) || candidateJid(out.wa_id);
      const sent = await safeSend(sock, target, out.message);
      await safeSend(
        sock, teamGroupJid,
        sent ? `✅ Sent to ${out.name || out.wa_id}:\n"${out.message}"`
             : `⚠️ Couldn't deliver to ${out.name || out.wa_id}.`,
      );
    } else {
      await safeSend(
        sock, teamGroupJid,
        `⚠️ ${out.note || "I couldn't identify that candidate — reply with their name or number, e.g. 'Ax, tell +1650… that …'"}`,
      );
    }
  } catch (e) {
    await safeSend(sock, teamGroupJid, `⚠️ Command failed: ${e.message}`);
  }
}

// Find the escalation group ("AX Reply") by name so we can post alerts to it.
async function resolveTeamGroup(sock) {
  try {
    const groups = await sock.groupFetchAllParticipating();
    for (const g of Object.values(groups || {})) {
      if ((g.subject || "").trim().toLowerCase() === TEAM_GROUP_NAME.toLowerCase()) {
        teamGroupJid = g.id;
        console.log(`👥 Escalation group "${TEAM_GROUP_NAME}" → ${teamGroupJid}`);
        return;
      }
    }
    console.log(`⚠️  Group "${TEAM_GROUP_NAME}" not found — add the bot's number to it. Falling back to team numbers.`);
  } catch (e) {
    console.log(`group lookup failed: ${e.message}`);
  }
}

// Build the formatted IMPORTANT alert for the team group.
function escalationAlert(name, waId, combined, out) {
  const c = (out.collected && typeof out.collected === "object") ? out.collected : {};
  const info = Object.entries(c)
    .filter(([k, v]) => v && !["booked", "ended", "name", "phone"].includes(k))
    .map(([k, v]) => `${k}: ${v}`).join(", ");
  // Prefer the real phone (from the lead form / WhatsApp key). Never show the raw
  // LID as a "number" — it isn't dialable and confuses the team.
  const phone = c.phone || "";
  const numberLine = phone
    ? `📱 *Number:* ${phone}  (wa.me/${phone.replace(/\D/g, "")})`
    : `📱 *Number:* not on file — reply to them inside WhatsApp (name: ${name || "candidate"})`;
  return (
    `🚨 *IMPORTANT — ${TEAM_GROUP_NAME}*\n` +
    `A candidate needs the team to follow up.\n\n` +
    `👤 *Name:* ${name || c.name || "Unknown"}\n` +
    `${numberLine}\n` +
    `📝 *Needs:* ${out.escalation_reason || "team follow-up"}\n` +
    (info ? `🗒️ *Info:* ${info}\n` : "") +
    `💬 *Their message:* "${combined}"`
  );
}

// Fires after a chat has been quiet for DEBOUNCE_MS: combine the buffered
// fragments and reply once.
async function flush(jid) {
  const entry = pending.get(jid);
  if (!entry) return;
  pending.delete(jid);
  const sock = currentSock;
  if (!sock || !entry.parts.length) return;

  const name = entry.name;
  const waId = jid.split("@")[0];
  const combined = entry.parts.join("\n");
  console.log(`💬 ${name || waId}: ${combined.replace(/\n/g, " / ")}`);

  try {
    const out = await askAgent(waId, combined, name, entry.phone);
    if (out.reply) {
      try { await sock.sendPresenceUpdate("composing", jid); } catch {}
      await sleep(replyDelayMs(out.reply));
      const sent = await safeSend(sock, jid, out.reply);
      try { await sock.sendPresenceUpdate("paused", jid); } catch {}
      if (sent) console.log(`🤖 → ${waId}: ${out.reply}`);
    }
    if (out.escalate) {
      const alert = escalationAlert(name, waId, combined, out);
      if (teamGroupJid) {
        try {
          const sent = await sock.sendMessage(teamGroupJid, { text: alert });
          rememberAlert(sent?.key?.id, { waId, name: (out.collected?.name || name || "") });
        } catch (e) {
          console.log("alert send failed: " + e.message);
        }
        console.log(`📣 escalation → group "${TEAM_GROUP_NAME}"`);
      } else if (Array.isArray(out.team_numbers) && out.team_numbers.length) {
        for (const num of out.team_numbers) await safeSend(sock, `${num}@s.whatsapp.net`, alert);
        console.log(`📣 escalation → team numbers (group "${TEAM_GROUP_NAME}" not found)`);
      } else {
        console.log(`⚠️  escalation but no group or team numbers configured`);
      }
    }
  } catch (e) {
    console.log(`⚠️  agent error: ${e.message}`);
    await safeSend(sock, jid, "Thanks for your message! Someone from our team will get back to you shortly.");
  }
}

async function start() {
  await loadTeamNumbers();

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    auth: state,
    logger,
    // Lets Baileys re-send a message when the recipient couldn't decrypt it,
    // instead of leaving them stuck on "Waiting for this message…".
    getMessage: async (key) => msgStore.get(key.id)?.message || undefined,
  });
  currentSock = sock;
  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      console.log("\n📱 Scan this QR in WhatsApp → Settings → Linked devices:\n");
      qrcode.generate(qr, { small: true });
      // Save the terminal QR as text too, so relink.sh can print it cleanly.
      qrcode.generate(qr, { small: true }, (ascii) => {
        try { fs.writeFileSync("qr.txt", ascii); } catch {}
      });
      // And a clean, scannable PNG (easier than scanning a terminal).
      QRImage.toFile("qr.png", qr, { width: 512, margin: 2 })
        .then(() => console.log('🖼️  QR image written to wa-bot/qr.png'))
        .catch((e) => console.log("   (couldn't write qr.png: " + e.message + ")"));
    }
    if (connection === "open") {
      console.log("\n✅ Connected. The bot is now auto-replying to incoming messages.\n");
      resolveTeamGroup(sock);
    }
    if (connection === "close") {
      const code = new Boom(lastDisconnect?.error)?.output?.statusCode;
      if (code === DisconnectReason.loggedOut) {
        console.log(`\n❌ Logged out. Delete the "${AUTH_DIR}" folder and re-run to re-link.\n`);
        notifyAlert(
          `⚠️ FutrBridge WhatsApp bot LOGGED OUT and stopped responding to candidates. ` +
          `It needs a fresh QR re-link to come back online.`,
        );
        return;
      }
      // Reconnect once, after a short delay, guarding against stacking sockets.
      if (reconnecting) return;
      reconnecting = true;
      console.log("🔄 Connection closed, reconnecting in 3s…");
      setTimeout(() => {
        reconnecting = false;
        start().catch((e) => console.log("reconnect failed: " + e.message));
      }, 3000);
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    for (const msg of messages) rememberMessage(msg); // for retry re-sends
    if (type !== "notify") return; // only brand-new messages, not history sync
    for (const msg of messages) {
      const jid = msg.key.remoteJid;
      if (!msg.message || msg.key.fromMe) continue;

      // Team group commands: either REPLY to an alert (we know the candidate), or
      // start a message with "Ax …". Handle it and move on; ignore the group otherwise.
      if (teamGroupJid && jid === teamGroupJid) {
        const t = extractText(msg);
        const quotedId = msg.message.extendedTextMessage?.contextInfo?.stanzaId;
        const ref = quotedId ? alertRefByMsgId.get(quotedId) : null;
        if (t && ref) {
          await handleGroupCommand(sock, msg, t, ref);
        } else if (t && /^\s*@?ax\b/i.test(t)) {
          await handleGroupCommand(sock, msg, t, null);
        }
        continue;
      }

      // Reply only to 1:1 chats. Individuals arrive as either @s.whatsapp.net or
      // @lid (WhatsApp's newer address format), so we DENYLIST the non-personal
      // types (groups, newsletters/channels, status/broadcast) instead of
      // allowlisting one — an allowlist wrongly dropped @lid users.
      if (!jid || jid.endsWith("@g.us") || jid.endsWith("@newsletter") || jid.endsWith("@broadcast")) continue;

      const waId = jid.split("@")[0];
      if (teamNumbers.has(waId)) continue; // don't chatbot our own team
      jidByWaId.set(waId, jid); // remember the real chat handle for later relays

      const name = msg.pushName || null;
      const m = msg.message;

      // Ignore promotional / interactive / broadcast message types — bank alerts,
      // "Pay Now" buttons, product cards, forwarded promos, stickers. A real
      // candidate types normal text; these are never worth replying to.
      if (m.templateMessage || m.buttonsMessage || m.interactiveMessage ||
          m.listMessage || m.productMessage || m.orderMessage || m.stickerMessage) {
        console.log(`🙈 ${name || waId}: [ignored promotional/interactive message]`);
        continue;
      }

      // Frequently-forwarded chain messages ("forward to 10 people…") → spam. Silent.
      if (forwardScore(msg) >= 4) {
        console.log(`🙈 ${name || waId}: [frequently-forwarded — likely spam, staying silent]`);
        continue;
      }

      let text = extractText(msg);

      // Voice note → download + transcribe with Gemini, then treat it like text.
      const audioMsg = m.audioMessage;
      if (audioMsg) {
        try {
          const buf = await downloadMediaMessage(msg, "buffer", {}, {
            logger, reuploadRequest: sock.updateMediaMessage,
          });
          const t = await transcribeAudio(buf.toString("base64"), audioMsg.mimetype || "audio/ogg");
          if (t) { text = t; console.log(`🎤 ${name || waId} (voice): ${text}`); }
        } catch (e) {
          console.log(`voice transcribe failed: ${e.message}`);
        }
        if (!text.trim()) {
          await safeSend(sock, jid, "Thanks for the voice note! I had a little trouble hearing it — mind typing your message?");
          continue;
        }
      }

      // A document with no caption is very likely a resume/CV — point them to the call.
      if (!text.trim() && m.documentMessage) {
        await safeSend(sock, jid, "Thanks for sharing! I can't open files here, but you can go over your resume with the team on the intro call. Happy to answer any questions in the meantime!");
        continue;
      }

      // Any other non-text with no caption (images, videos, unknown) → stay silent.
      // Could easily be spam or a forward; a real candidate will type. Don't reply.
      if (!text.trim()) {
        console.log(`🙈 ${name || waId}: [non-text, no caption — staying silent]`);
        continue;
      }

      try { await sock.readMessages([msg.key]); } catch {} // mark read, like a person

      // Buffer this fragment and (re)start the debounce timer. When the person
      // stops typing for DEBOUNCE_MS, flush() answers the whole burst at once.
      const entry = pending.get(jid) || { parts: [], timer: null, name, phone: "" };
      entry.parts.push(text);
      entry.name = name;
      if (!entry.phone) entry.phone = phoneFromKey(msg);
      if (entry.timer) clearTimeout(entry.timer);
      entry.timer = setTimeout(
        () => flush(jid).catch((e) => console.log("flush error: " + e.message)),
        DEBOUNCE_MS,
      );
      pending.set(jid, entry);
    }
  });
}

start().catch((e) => {
  console.error("Fatal:", e);
  process.exit(1);
});
