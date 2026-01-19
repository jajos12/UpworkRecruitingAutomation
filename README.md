# Upwork Recruitment Agent (UpworkHireBot)

An AI-powered automation tool designed to transform the Upwork hiring process. This agent handles the heavy lifting of recruiting by extracting applicant data, analyzing proposals with LLMs, and automating communication, surfacing only the most qualified candidates who strictly meet your criteria.

## 🚀 Features

- **Automated Data Extraction**: Pulls jobs, proposals, and freelancer profiles directly from Upwork using their API.
- **AI-Powered Analysis**: Uses advanced LLMs (Claude, OpenAI, or Gemini) to evaluate candidates against specific job criteria.
    - Scores candidates (0-100).
    - Classifies them into Tiers (1: excellent, 2: maybe, 3: pass).
    - Generates detailed reasoning and recommendations.
- **Smart Filtering**: Automatically identifies "Must Have" requirements and "Red Flags".
- **Communication Automation**: Handles initial responses and scheduling for qualified candidates.
- **Dual Interface**:
    - **CLI**: Robust command-line tool for background execution and daemon mode.
    - **Web Dashboard**: Modern frontend to view jobs, proposals, and AI analysis results in real-time.

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Pydantic.
- **AI**: Anthropic (Claude), OpenAI (GPT-4), Google (Gemini) integration.
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla).
- **Database**: SQLite (via SQLAlchemy).
- **Process Management**: Tenacity (retries), APScheduler (if used internally), Python-multipart.

## 📋 Prerequisites

- Python 3.10 or higher.
- An Upwork Client Account (and API keys if using real extraction).
- API Keys for at least one AI provider (Anthropic, OpenAI, or Google).

## ⚡ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/upworkRecruitmentAgent.git
    cd upworkRecruitmentAgent
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**
    Copy the example environment file and fill in your credentials.
    ```bash
    cp .env.example .env
    ```
    Edit `.env` with your API keys:
    ```ini
    # AI Providers
    AI_PROVIDER=claude  # or openai, gemini
    ANTHROPIC_API_KEY=sk-ant-...
    OPENAI_API_KEY=sk-...

    # Upwork API (if connected)
    UPWORK_API_KEY=...
    ```

## 🏃 Usage

### Command Line Interface (CLI)

The CLI is the primary engine for the automation pipeline.

```bash
# Run a single pass of the full pipeline (Fetch -> Analyze -> Communicate)
python src/main.py

# Run in daemon mode (continuously checks every 15 minutes)
python src/main.py --daemon

# Fetch data only (no analysis)
python src/main.py --fetch-only

# Analyze existing data only
python src/main.py --analyze-only

# Dry run (simulate actions without sending messages)
python src/main.py --dry-run
```

### Web Dashboard

Start the backend server to access the UI.

```bash
uvicorn backend.app:app --reload
```
Open your browser to `http://localhost:8000`.

## 📂 Project Structure

```
├── backend/            # FastAPI web server and API endpoints
│   ├── app.py          # Server entry point
│   ├── models.py       # Pydantic models
│   └── database.py     # Database connection
├── frontend/           # Web dashboard UI
│   ├── index.html
│   └── js/
├── src/                # Core business logic
│   ├── ai_analyzer.py  # AI evaluation logic
│   ├── pipeline.py     # Main automation orchestration
│   ├── upwork_client.py # Upwork API integration
│   └── main.py         # CLI entry point
├── PRD.md              # Product Requirements Document
└── requirements.txt    # Python dependencies
```

## 🤝 Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 📄 License

[MIT License](LICENSE)
