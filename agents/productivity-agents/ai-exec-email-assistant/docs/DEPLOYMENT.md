# 🚀 Deployment Guide

Three supported paths: **Streamlit Community Cloud**, **Docker**, and a **plain VM**.

---

## Option A — Streamlit Community Cloud (fastest)

1. Push the repo to GitHub (the `.gitignore` already excludes secrets).
2. Go to <https://share.streamlit.io>, click **New app**, pick the repo and
   `app.py`.
3. In **Advanced settings → Secrets**, paste your env vars in TOML form:

   ```toml
   OPENAI_API_KEY = "sk-..."
   OPENAI_MODEL = "gpt-4o-mini"
   GOOGLE_CLIENT_ID = "xxx.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "xxx"
   GOOGLE_REDIRECT_URI = "https://your-app.streamlit.app"
   ENABLE_VOICE = "true"
   ```

   > Streamlit secrets are exposed as environment variables, so `config/settings.py`
   > reads them transparently. No code changes needed.

4. Add `https://your-app.streamlit.app` as an **Authorized redirect URI** in the
   Google Cloud Console (see `OAUTH_SETUP.md`).
5. Deploy. Done.

> **⚠️ Monorepo note (important if your repo holds multiple apps).** If this
> project lives in a subfolder (e.g.
> `amazing-ai-agents/agents/.../ai-exec-email-assistant/app.py`), Streamlit
> Cloud installs dependencies from a `requirements.txt` it can find at the
> **repo root** or **next to the main file**. If yours is only inside this
> subfolder and the root has a different one, you'll get
> `ImportError: No module named 'openai'` (or similar) on launch. Fix by either:
> (a) setting the app's **Main file path** to this folder's `app.py` AND keeping
> `requirements.txt` beside it, or (b) copying/merging this `requirements.txt`
> into the repo root. The in-app **Settings → Diagnostics** panel shows exactly
> which packages are present so you can confirm the fix.

**Note on token persistence:** Community Cloud has an ephemeral filesystem, so
`.tokens/` resets on restart — users simply re-auth. For durable tokens, use a
VM/Docker volume or store the token in Streamlit secrets / a managed DB.

---

## Option B — Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build & run (mount a volume so the SQLite cache and tokens persist):

```bash
docker build -t email-assistant .
docker run -p 8501:8501 --env-file .env \
  -v $(pwd)/data:/app/database \
  -v $(pwd)/.tokens:/app/.tokens \
  email-assistant
```

Set `GOOGLE_REDIRECT_URI` to your public URL and register it in Google Cloud.

---

## Option C — VM (Ubuntu) with systemd

```bash
# On the VM
sudo apt update && sudo apt install -y python3-venv
git clone <your-repo> && cd ai-exec-email-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env   # fill in values
```

Create `/etc/systemd/system/email-assistant.service`:

```ini
[Unit]
Description=AI Executive Email Assistant
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/ai-exec-email-assistant
ExecStart=/home/ubuntu/ai-exec-email-assistant/.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now email-assistant
```

Put **nginx** (or Caddy) in front for HTTPS, then set
`GOOGLE_REDIRECT_URI=https://your-domain` and register it in Google Cloud.

---

## Production checklist

- [ ] HTTPS in front of the app (OAuth requires it for non-localhost).
- [ ] `GOOGLE_REDIRECT_URI` matches the Console exactly.
- [ ] Secrets injected via the platform's secret store, never committed.
- [ ] Persistent volume for `database/` and `.tokens/` if you want token reuse.
- [ ] Publish the OAuth consent screen if more than a handful of users.
- [ ] Set `LOG_LEVEL=INFO` (or `WARNING`) and ship logs somewhere.
- [ ] Monitor OpenAI spend; tune `OPENAI_MODEL` / `MAX_EMAILS_FETCH` for cost.
