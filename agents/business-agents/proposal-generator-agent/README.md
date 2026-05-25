# 📝 AI Proposal Generator Agent

> Fill in 5 fields → GPT-4o generates a complete professional business proposal with scope, pricing, timeline, terms, and case study — export as branded PDF or DOCX in seconds.

---

<div align="center">

⭐ **[Star the repo](https://github.com/adityasharmadotai-hash)** &nbsp;·&nbsp;
🌐 **[adityasharma.ai](https://www.adityasharma.ai)** &nbsp;·&nbsp;
💼 **[LinkedIn](https://www.linkedin.com/in/aditya-hicounselor/)** &nbsp;·&nbsp;
📺 **[YouTube](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)** &nbsp;·&nbsp;
🚀 **[AI Jobs USA](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)**

</div>

---

**👉 STEP-BY-STEP TUTORIAL: [Tutorial.md](./Tutorial.md)**

---

## Features

| Feature | Description |
|---------|-------------|
| ✨ **5 Templates** | Agency, SaaS, Consulting, Marketing, Development |
| 🤖 **Full AI Generation** | GPT-4o writes all 12 proposal sections in one call |
| 📋 **Scope of Work** | Phased breakdown with deliverables per phase |
| 💰 **3 Pricing Packages** | Starter, Professional, Enterprise with recommended highlight |
| 📅 **Project Timeline** | 5-milestone schedule from kickoff to delivery |
| ⚖️ **Terms & Conditions** | 7 legal clauses auto-generated |
| 🔄 **Section Regeneration** | Rewrite any section with custom instructions |
| ✉️ **Cover Letter** | AI-generated email to accompany the proposal |
| ⚡ **Quick Pricing Estimator** | Budget estimate before full generation |
| 📄 **PDF Export** | Branded ReportLab PDF with tables and color scheme |
| 📝 **DOCX Export** | Editable Word document |
| 🎨 **Branding** | Custom colors, logo upload, agency identity |
| 👥 **Client Management** | Client history and proposal tracking |
| 📊 **Analytics Dashboard** | Win rate, status breakdown, template usage |

## Quick Start

```bash
pip install -r requirements.txt
echo 'OPENAI_API_KEY=sk-...' > .env
streamlit run app.py
```

## Deploy to Streamlit Cloud

```toml
OPENAI_API_KEY = "sk-your-key"
```

## Structure

```
proposal-agent/
├── app.py                 # 6-page Streamlit UI
├── modules/
│   ├── generator.py       # GPT-4o proposal generation
│   ├── storage.py         # Session-state storage
│   └── exporter.py        # PDF + DOCX export
├── requirements.txt
└── .env.example
```

## Cost

~$0.05 per complete proposal (5 GPT-4o calls total)

---

*Built with ❤️ by [Aditya Sharma](https://www.adityasharma.ai)*
