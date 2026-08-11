#!/usr/bin/env bash
# Re-link the WhatsApp bot to a phone — after a logout, or to switch numbers.
#
# Usage (on the server):
#   su - claude-temp
#   ~/whatsapp-agent/relink.sh
#
# It clears the old session, restarts the bot, and prints a fresh QR to scan.
set -e
export PATH="$HOME/node22/bin:$PATH"
cd "$HOME/whatsapp-agent/wa-bot"

echo "→ Clearing old WhatsApp session and restarting the bot…"
rm -rf auth qr.png qr.txt
pm2 restart wa-bot >/dev/null 2>&1 || pm2 start index.js --name wa-bot --interpreter "$HOME/node22/bin/node" >/dev/null 2>&1

echo "→ Waiting for a fresh QR…"
for _ in $(seq 1 30); do [ -f qr.txt ] && break; sleep 1; done

echo ""
echo "==================  SCAN THIS QR  =================="
echo "WhatsApp → Settings → Linked devices → Link a device"
echo "(Maximize this terminal window so the QR isn't cut off.)"
echo ""
if [ -f qr.txt ]; then
  cat qr.txt
else
  echo "(QR not ready yet — run:  pm2 logs wa-bot --raw  and scan it there)"
fi
echo ""
echo "After scanning, it auto-connects and saves the session — you're done."
echo "If the QR expired before you scanned, just run ~/whatsapp-agent/relink.sh again."
