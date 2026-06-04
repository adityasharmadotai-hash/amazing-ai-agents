# 📰 Newsletter Content Creation Agent

Generate complete, ready-to-send newsletters from the latest online news — in one click. The agent researches recent articles with **NewsAPI**, summarizes and extracts insights with **OpenAI GPT-4o**, and writes a full edition (title, subject line, intro, key insights, conclusion, CTA) you can preview, copy, and download as Markdown.

Part of the **amazing-ai-agents** series.

---

## ✨ Features

| Area | What it does |
|------|--------------|
| **Settings** | Store OpenAI + NewsAPI keys and default preferences, saved locally in SQLite |
| **User Input** | Topic, target audience, writing style, content length |
| **Content Research** | Fetches recent news via NewsAPI, removes duplicates, selects top 5 articles |
| **AI Processing** | Summarizes each article, extracts key insights, writes the newsletter |
| **Generation** | Newsletter title, subject line, introduction, key insights, conclusion, CTA |
| **Dashboard** | One-click generate, live preview, copy button, download as Markdown |
| **History** | Every generated edition is saved and re-openable |
| **UI** | Clean modern dark Streamlit UI with sidebar navigation |

---

## 🧱 Architecture

```
newsletter-agent/
├── app.py                  # Streamlit entry point + page router
├── modules/
│   ├── database.py         # SQLite: settings + newsletter history
│   ├── news.py             # NewsAPI fetch, dedupe, top-N selection
│   ├── ai.py               # OpenAI GPT-4o summarize + generate
│   ├── newsletter.py       # Structured output -> Markdown
│   ├── styles.py           # Custom CSS + copy-to-clipboard component
│   └── seed.py             # Demo newsletters so the dashboard isn't empty
├── .streamlit/config.toml  # Dark theme
├── requirements.txt
└── README.md
```

---

## 🚀 Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Then in the app:
1. Open **⚙️ Settings** → paste your **OpenAI** and **NewsAPI** keys → Save.
2. Go to **✍️ Create Newsletter** → enter topic, audience, style, length → **Generate**.
3. Preview, **Copy**, or **Download** the Markdown.

---

## 🔑 API keys

- **OpenAI** — https://platform.openai.com (uses the `gpt-4o` model)
- **NewsAPI** — https://newsapi.org (free developer tier works for testing)

Keys are stored in a local `newsletter.db` SQLite file and never leave your machine. `newsletter.db` is git-ignored.

> **Note:** NewsAPI's free Developer plan only returns articles from the last ~30 days and is limited to non-production/localhost use — perfect for this tool.

---

## 🛠️ Tech stack

- **Python** + **Streamlit** (UI)
- **OpenAI GPT-4o** (summarization + writing)
- **NewsAPI** (content research)
- **SQLite** (local persistence)

---

## 📄 License

MIT — build on it freely.
