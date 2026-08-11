/**
 * pm2 process manager config — runs the WhatsApp agent 24/7 with auto-restart.
 *
 * On your server (Node + Python installed, deps installed):
 *   npm i -g pm2
 *   pm2 start ecosystem.config.cjs
 *   pm2 logs wa-bot          # watch the QR on first run, scan it once
 *   pm2 save && pm2 startup  # survive reboots
 *
 * Both processes must run on the SAME machine/volume so they share
 * data/whatsapp.db and wa-bot/auth (the WhatsApp session must persist).
 */
module.exports = {
  apps: [
    {
      name: "wa-agent-server",
      script: "agent_server.py",
      interpreter: "python3", // use "python" on Windows
      cwd: __dirname,
      autorestart: true,
      max_restarts: 50,
      restart_delay: 3000,
    },
    {
      name: "wa-bot",
      script: "index.js",
      cwd: __dirname + "/wa-bot",
      interpreter: "node",
      autorestart: true,
      max_restarts: 50,
      restart_delay: 5000,
    },
  ],
};
