# Titanic Agent

This project is a **Proof-of-Concept AI Agent** specialized in the Titanic dataset.  
It demonstrates how an AI agent can integrate **short-term memory, visualization, and predictive modeling** to provide an interactive experience.

---

## Features
1. **Short-term memory** – remembers the context of your queries within a session.
2. **Visualization** – generates plots and charts based on the Titanic dataset.
3. **Real-time prediction** – given a passenger profile (e.g., *“a 30-year-old female in third class”*), the agent predicts survival probability and provides visual explanations.

⚠️ Note:  
This project is **for demonstration purposes only (POC-level)**.  
It is **not designed for production use** and does not consider production-grade system architecture, scaling, or security requirements.  
The goal is to showcase what modern AI agents can look like.

---

## Getting Started

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd Titanic-Agent
```

### 2. Create a `.env` File
Inside the project root, create a `.env` file with the following content:
```env
OPENAI_API_KEY=your_api_key_here
```

### 3. Initialize the Database
Run the script to create the local SQLite database (`titanic.db`):
```bash
python -m app.db.init_db
```

### 4. Build and Run with Docker Compose
```bash
docker compose up --build
```

After the service starts, open your browser and visit:
```
http://localhost:1111
```

You should now see the **Titanic Agent** interface.

---

## Example Usage
You can ask questions like:
- *“Show me a survival prediction for a 30-year-old female in third class.”*  
- *“Plot the age distribution of survivors and non-survivors.”*  
- *“What’s the survival rate for first-class passengers under 18?”*  

The agent will provide both **predictions** and **visualizations** in real time.

---

## Tech Stack
- **Python 3.12**
- **Streamlit** (frontend)
- **SQLite** (Titanic dataset storage)
- **Docker & Docker Compose** (easy deployment)
- **OpenAI API** (LLM reasoning and memory)

## Project Structure
```text
sql_agent/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── schemas/
│   └── utils/
├── data/
├── model/
├── notebooks/
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── README.md
```

---

## Disclaimer
This project is **experimental and educational**.  
It is intended to illustrate how AI agents can be built with modern tools.  
**Do not use it in production** without significant modifications.
