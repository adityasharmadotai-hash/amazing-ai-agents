# 🔐 Google OAuth Setup Guide

This app needs OAuth credentials to access Gmail and Google Calendar on your
behalf. Follow these steps once.

## 1. Create / select a Google Cloud project

1. Go to <https://console.cloud.google.com/>.
2. Top bar → project dropdown → **New Project** (or pick an existing one).
3. Give it a name like `email-assistant` and create it.

## 2. Enable the APIs

In **APIs & Services → Library**, enable both:

- **Gmail API**
- **Google Calendar API**

(Search each by name and click **Enable**.)

## 3. Configure the OAuth consent screen

1. **APIs & Services → OAuth consent screen**.
2. User type: **External** (unless you have a Workspace org → Internal).
3. Fill app name, user support email, developer email.
4. **Scopes** — you can leave default; the app requests these at runtime:
   - `gmail.modify`, `gmail.compose`
   - `calendar.readonly`
   - `userinfo.email`, `userinfo.profile`, `openid`
5. **Test users** — while your app is in *Testing* mode, add the Google
   account(s) you'll sign in with. (Publishing is only needed for many users.)

## 4. Create OAuth client credentials

1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Web application**.
3. **Authorized redirect URIs** — add the URL the app runs on:
   - Local: `http://localhost:8501`
   - Deployed: `https://your-app.streamlit.app` (exact, no trailing slash)
4. Create. Copy the **Client ID** and **Client secret**.

> The redirect URI in Google Cloud **must exactly match** `GOOGLE_REDIRECT_URI`
> in your `.env`. Mismatches are the #1 cause of `redirect_uri_mismatch` errors.

## 5. Put the credentials in `.env`

```env
GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8501
```

**Alternative:** download the client secret JSON and point to it instead:

```env
GOOGLE_CLIENT_SECRETS_FILE=/absolute/path/to/client_secret.json
```

## 6. (Optional) Local "installed app" flow

For quick local testing without redirect handling, the app also supports
`run_local_flow()` in `services/auth_service.py`, which spins up a temporary
local server and opens a browser. The web flow above is recommended for parity
with deployment.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `redirect_uri_mismatch` | Make `GOOGLE_REDIRECT_URI` identical to the Console entry. |
| `access_denied` | Add your account under **Test users** on the consent screen. |
| `invalid_grant` on refresh | Delete `.tokens/token.json` and sign in again. |
| Scopes changed, weird behaviour | Delete `.tokens/` and re-auth so the new scopes are granted. |
