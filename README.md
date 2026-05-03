# Titanic Agent

A **Proof-of-Concept AI Agent** for the Titanic dataset.  
Ask questions in natural language — the agent queries SQLite, runs ML predictions, and returns ECharts visualizations or text summaries.

---

## Features

1. **Short-term memory** – remembers context within a session
2. **Visualization** – generates charts based on the Titanic dataset
3. **Real-time prediction** – given a passenger profile, predicts survival probability with visual explanation

⚠️ This project is for **demonstration purposes only**. Not intended for production use.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd SQL_agent
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Then open `.env` and fill in your OpenAI API key:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o   # optional, defaults to gpt-4o
```

### 3. Start with Docker Compose

```bash
docker compose up --build
```

The database is initialized automatically on first start. Once running, open:

```
http://localhost:1111
```

---

## Example Queries

- *"Show me a survival prediction for a 30-year-old female in third class."*
- *"Plot the age distribution of survivors and non-survivors."*
- *"What's the survival rate for first-class passengers under 18?"*

---

## Tech Stack

| | |
|---|---|
| API | FastAPI + Uvicorn |
| LLM | OpenAI gpt-4o (tool calling) |
| DB | SQLite |
| ML | scikit-learn (fit per request, no persistence) |
| Frontend | Streamlit + streamlit-echarts |
| Container | Docker Compose |

## Project Structure

```text
SQL_agent/
├── app/
│   ├── api/
│   │   ├── routes/       # Router layer (HTTP only)
│   │   └── schemas/      # Pydantic request/response models
│   ├── services/         # Service layer (business logic)
│   ├── db/
│   │   └── dao/          # DAO layer (SQLite access + ML)
│   ├── config/           # Settings & constants
│   ├── utils/
│   └── web/              # Streamlit frontend
├── data/                 # train.csv
├── model/                # titanic.db (generated at runtime)
├── docker-compose.yml
├── Dockerfile
└── Makefile
```

---

## Disclaimer

Experimental and educational. Do not use in production without significant modifications.
