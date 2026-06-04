# 🧭 Tutorial — Newsletter Content Creation Agent

A step-by-step walkthrough of how the agent works and how to use it.

---

## 1. The pipeline

When you click **Generate**, four things happen in sequence:

```
Topic ──► [NewsAPI]  ──► fetch ~30 recent articles
                          │
                          ▼
                     dedupe + pick top 5   (modules/news.py)
                          │
                          ▼
        [GPT-4o]  ──► summarize each article + extract a key point
                          │                  (modules/ai.summarize_articles)
                          ▼
        [GPT-4o]  ──► write the newsletter as structured JSON
                          │                  (modules/ai.generate_newsletter)
                          ▼
                     assemble Markdown        (modules/newsletter.py)
                          │
                          ▼
                preview · copy · download · save to history
```

---

## 2. Setup (one time)

1. Get an **OpenAI API key** at platform.openai.com.
2. Get a free **NewsAPI key** at newsapi.org.
3. Run the app: `streamlit run app.py`
4. Open **⚙️ Settings**, paste both keys, set any default preferences, and **Save**.

Settings persist in a local SQLite file, so you only do this once.

---

## 3. Creating a newsletter

On the **✍️ Create Newsletter** page you provide four inputs:

| Input | Example | Effect |
|-------|---------|--------|
| **Topic** | `AI agents` | The NewsAPI search query |
| **Audience** | `AI engineers and founders` | Steers tone and framing |
| **Style** | `Professional` / `Casual` / `Storytelling` / `Technical` / `Witty` / `Inspirational` | Sets the voice |
| **Length** | `Short` / `Medium` / `Long` | Maps to a word budget (~300 / ~600 / ~1000 words) |

You can also choose how many articles to research (3–5).

Click **✨ Generate Newsletter** and watch the live status panel walk through research → summarizing → writing.

---

## 4. The output

You get a full edition:

- **Title** — a catchy newsletter headline
- **Subject line** — optimized for an email open
- **Introduction** — a warm, on-topic opener
- **Key insights** — 3–5 sections, each with a heading and paragraph
- **Conclusion** — a tidy wrap-up
- **CTA** — one clear call-to-action
- **Sources** — links to the researched articles

Use the **Preview** tab for the rendered version, the **Markdown** tab for raw text, then **📋 Copy** or **⬇️ Download as Markdown**.

Every edition is auto-saved to **🗂️ History**, where you can re-open, download, or delete it.

---

## 5. Customizing

- **Change the model:** edit `MODEL` in `modules/ai.py` (e.g. `gpt-4o-mini` for cheaper runs).
- **Tune length:** edit `LENGTH_GUIDE` in `modules/ai.py`.
- **Add styles:** append to the `STYLES` list in `app.py`.
- **Adjust research depth:** `news.research(topic, key, count=...)`.
- **Restyle the UI:** edit the `CSS` block in `modules/styles.py`.

---

## 6. Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Add API keys in Settings" | Keys not saved — re-enter in Settings |
| "NewsAPI rejected the key (401)" | Wrong/expired NewsAPI key |
| "NewsAPI rate limit reached (429)" | Free tier limit hit — wait and retry |
| "No usable articles" | Topic too narrow — try a broader query |
| "OpenAI ... failed" | Check the key, billing, and model access |

---

Built as part of the **amazing-ai-agents** series. PRs welcome.
