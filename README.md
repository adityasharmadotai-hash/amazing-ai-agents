 # 🚀 Amazing AI Agents

Hi! I'm Aditya Sharma — a serial entrepreneur and AI engineer based in San Francisco.

I created this repository to help you go from knowing nothing about AI agents to building production-ready AI agent systems through hands-on, open-source projects.


<div align="center">

![GitHub Stars](https://img.shields.io/github/stars/adityasharmadotai-hash/amazing-ai-agents?style=for-the-badge&logo=github&color=FFD43B)
![GitHub Forks](https://img.shields.io/github/forks/adityasharmadotai-hash/amazing-ai-agents?style=for-the-badge&logo=github)
![GitHub Issues](https://img.shields.io/github/issues/adityasharmadotai-hash/amazing-ai-agents?style=for-the-badge&logo=github)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python)

[![Star the Repo](https://img.shields.io/badge/⭐_Star_this_repo-amazing--ai--agents-FFD43B?style=for-the-badge&logo=github&logoColor=black)](https://github.com/adityasharmadotai-hash/amazing-ai-agents)
[![Follow on LinkedIn](https://img.shields.io/badge/💼_LinkedIn-aditya--hicounselor-0A66C2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/aditya-hicounselor/)
[![Subscribe on YouTube](https://img.shields.io/badge/📺_YouTube-@adityasharma-FF0000?style=for-the-badge&logo=youtube)](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)

</div>

---

## 📌 What Are AI Agents?

AI Agents are autonomous software systems that use large language models (LLMs) to perceive their environment, make decisions, and take actions toward a goal. Unlike simple chatbots, agents can:


---

## 💡 Learning Roadmap

### Single-Agent Systems

| Project | Link |
|---------|------|
| Proposal Generator Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/business-agents/proposal-generator-agent) |
| Founder Daily Brief Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/business-agents/founder-daily-brief-agent) |
| Skill Gap Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/career-agents/skill-gap-agent) |
| Content Repurposing Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/content-agents/content-repurposing-agent) |
| Newsletter Content Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/content-agents/newsletter-content-agent) |
| SEO Audit Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/marketing-agents/seo-audit-agent) |
| LinkedIn Opportunity Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/networking-agents/linkedin-opportunity-agent) |
| Email Assistant | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/productivity-agents/email-assistant) |
| Email Summary & Action Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/productivity-agents/email-summary-action-agent) |
| AI Exec Email Assistant | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/productivity-agents/ai-exec-email-assistant) |
| Layoff Detection (LinkedIn) Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/layoff-detection-linkedin) |

### Multi-Agent Systems

| Project | Link |
|---------|------|
| Multi-MCP Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/mcp-agents/multi-mcp-agent) |
| AI Database Analyst (MCP) | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/mcp-agents/ai-database-analyst-mcp) |
| AI Sales Team | [Click here](https://github.com/adityasharmadotai-hash/networking-app) |

### RAG (Retrieval-Augmented Generation) AI Agents

| Project | Link |
|---------|------|
| Docs Reader RAG Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/rag-agents/docs-reader-rag-agent) |

### Voice AI Agents

| Project | Link |
|---------|------|
| Voice Assistant Agent (ARIA) | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/productivity-agents/voice-assistant-agent) |
| Meeting Notes Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/productivity-agents/meeting-notes-agent) |

### Document AI Agents

| Project | Link |
|---------|------|
| Resume ↔ Job Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/recruiting-agents/resume-job-agent) |

### Research AI Agents

| Project | Link |
|---------|------|
| Competitor Intelligence Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/research-agents/competitor-intelligence-agent) |
| AI News Summary Agent | [Click here](https://github.com/adityasharmadotai-hash/amazing-ai-agents/tree/main/agents/productivity-agents/ai-news-summary-agent) |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (or Claude API key for some agents)
- 2GB RAM minimum
- Internet connection for API calls

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies for your chosen agent:**
```bash
cd agents/business-agents/proposal-generator-agent
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run the agent:**
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 🛠️ Tech Stack Overview

### Core Frameworks & Libraries
- **Streamlit** — Fast web UI framework for data apps
- **OpenAI API** — GPT-4o, Whisper, Text-to-Speech
- **Claude API** — Alternative LLM for some agents
- **LangChain / LangGraph** — Agentic workflows (in some agents)

### Backend & Data
- **FastAPI** — Rest API for agent backends
- **SQLite / PostgreSQL** — Data persistence
- **Supabase** — Real-time database + auth
- **ChromaDB / Pinecone** — Vector databases for RAG

### Integrations
- **Gmail API** — Email access & automation
- **Google Calendar API** — Meeting management
- **Google Sheets API** — Data export
- **WhatsApp API** — Message delivery
- **NewsAPI** — News aggregation
- **BeautifulSoup4** — Web scraping

### AI & ML
- **OpenAI Whisper** — Speech-to-text
- **OpenAI TTS** — Text-to-speech
- **Sentence Transformers** — Embeddings for RAG
- **LangChain** — LLM orchestration

---

## 📖 Getting Help

Each agent has:
- **README.md** — Quick start & features
- **Tutorial.md** — Step-by-step setup guide
- **requirements.txt** — All dependencies
- **Example .env** — Environment variable template

For each agent, start with the Tutorial → then explore the code.

---

## 🌐 Community & Contributing

### How to Contribute
1. **Report Bugs** — Open an issue with reproducible steps
2. **Suggest Features** — Use discussions for feature requests
3. **Submit PRs** — Fork → create feature branch → submit PR
4. **Improve Docs** — Help us translate or improve documentation

### Code of Conduct
- Be respectful and inclusive
- Help others learn
- Give credit to contributors
- Share knowledge freely

### Development Setup
```bash
git clone https://github.com/adityasharmadotai-hash/amazing-ai-agents.git
cd amazing-ai-agents
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

---

## 🔗 Connect & Support

<div align="center">

### ⭐ Show Your Support

[![Star the Repo](https://img.shields.io/badge/⭐_Star_this_repo-amazing--ai--agents-FFD43B?style=for-the-badge&logo=github&logoColor=black)](https://github.com/adityasharmadotai-hash/amazing-ai-agents)

### 💼 Follow & Subscribe

[![LinkedIn](https://img.shields.io/badge/LinkedIn-aditya--hicounselor-0A66C2?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/aditya-hicounselor/)

[![YouTube](https://img.shields.io/badge/YouTube-@adityasharma-FF0000?style=for-the-badge&logo=youtube)](https://www.youtube.com/channel/UCPjQtVNUrf7EKrm8ZoqrCAQ)

### 🚀 AI Job Opportunities

[![Apply Now](https://img.shields.io/badge/🚀_Top_AI_Jobs_in_USA-Apply_Now-green?style=for-the-badge)](https://docs.google.com/forms/d/e/1FAIpQLSc3gJssBV3B25EZ3sYA7Qcen9NbtOB_wgQaturfB7lTXuAdLQ/viewform)

---

📧 **Email:** [aditya@adityasharma.ai](mailto:aditya@adityasharma.ai)

🌐 **Website:** [adityasharma.ai](https://www.adityasharma.ai)

</div>

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

You are free to:
- ✅ Use commercially
- ✅ Modify & distribute
- ✅ Use privately
- ✅ Add disclaimers

---

<div align="center">

### Made with ❤️ by [Aditya Sharma](https://www.adityasharma.ai)

**Explore. Learn. Build. Deploy.**

</div>