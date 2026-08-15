# Autonomous Financial Research Agent for BFSI

An autonomous, multi-tool AI agent system designed for Banking, Financial Services, and Insurance (BFSI) use cases. Powered by Google Gemini (Free Tier), this agent conducts deep financial research across SEC filings (10-K, 10-Q), earnings call transcripts, market data, and regulatory disclosures to produce synthesized, publication-grade financial analysis reports.

## 🎯 Key Objectives & Capabilities

- **SEC Filings Analysis**: Extraction, parsing, and financial ratio analysis from SEC EDGAR 10-K, 10-Q, and 8-K disclosures.
- **Earnings Transcript Processing**: Qualitative sentiment tracking, executive guidance extraction, and Q&A topic breakdown.
- **Multi-Source Synthesis**: Cross-referencing quantitative financial metrics with qualitative disclosure narrative and macroeconomic data.
- **Agent Memory System**: Episodic and semantic memory architectures for historical context retention and cross-quarter tracking.
- **Structured Report Generation**: Generating standardized institutional research notes, risk matrices, and valuation context summaries.
- **Rigorous Evaluation Suite**: Domain-specific evaluation framework designed to score factual precision, numeric accuracy, hallucination resistance, and analytical depth.

## 🏗️ Project Architecture

```
financial-research-agent/
├── agent/
│   ├── config.py      # Environment validation & Pydantic settings schema
│   ├── tools/         # Autonomous agent tools (SEC APIs, market data, parsers)
│   ├── memory/        # Episodic, semantic, and working memory stores
│   ├── synthesis/     # Multi-source intelligence & reconciliation engines
│   └── reporting/     # Structured research report generators & formatters
├── eval/
│   └── challenges/    # Benchmark evaluation cases and financial test suites
├── scripts/
│   └── check_setup.py # System setup & environment verification script
├── tests/             # Unit and integration test suite
├── examples/          # Executable usage scripts and end-to-end demonstrations
├── cache/             # Local data and document cache
├── .env.example       # Environment configuration template
├── CHANGELOG.md       # Version history and phase progression tracking
├── requirements.txt   # Project dependencies
└── README.md          # Project overview & documentation
```

## 🛠️ Tech Stack & Conventions

- **Language**: Python 3.11+
- **LLM Engine**: Google Gemini API (`gemini-2.0-flash`) via `google-genai` / `google-generativeai`
- **Data Models**: Pydantic v2 for strict type safety and schema validation
- **Configuration**: `python-dotenv` for secure environment variable management
- **Vector DB**: ChromaDB for local embedding storage
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Testing**: Pytest unit and integration test coverage
- **Design Philosophy**: Modular architecture where every component is independently testable, reusable, and clearly documented.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git

### Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/financial-research-agent.git
   cd financial-research-agent
   ```

2. **Activate the Virtual Environment**:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file from the provided `.env.example` template:
   ```bash
   cp .env.example .env
   ```

### 🔑 Environment Variables & API Key Overview

| Variable | Description | Source / Requirement |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini API key for LLM reasoning | **Required (Free Tier)**. Obtain at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | Gemini LLM model identifier | Optional (Default: `gemini-2.0-flash`) |
| `SEC_EDGAR_USER_AGENT` | User-Agent required by SEC EDGAR Fair Access rules | **Required**. Format: `YourName your.email@example.com` |
| `EMBEDDING_MODEL` | Local HuggingFace embedding model | Optional (Default: `all-MiniLM-L6-v2`, local execution) |
| `CHROMA_DB_PATH` | Local ChromaDB vector database directory | Optional (Default: `./cache/chroma_db`) |
| `FMP_API_KEY` | Financial Modeling Prep key for transcripts | Optional (Free tier 250 req/day at [financialmodelingprep.com](https://site.financialmodelingprep.com/)) |
| `ALPHA_VANTAGE_API_KEY`| Alpha Vantage key for market data | Optional (Free tier 25 req/day at [alphavantage.co](https://www.alphavantage.co/)) |
| `FINNHUB_API_KEY` | Finnhub key for financial news & earnings | Optional (Free tier at [finnhub.io](https://finnhub.io/)) |

### 🧪 System Setup Diagnostic Verification

Run the automated diagnostic check script at any time to verify your environment, API keys, local embedding model, and ChromaDB persistent storage:

```bash
python scripts/check_setup.py
```

## 📜 Roadmap & Build Phases

- [x] **Phase 0**: Project Setup & Environment Configuration Engine (Google Gemini Free Tier)
- [ ] **Phase 1**: Tool Registry & SEC Filing Retrieval Engine
- [ ] **Phase 2**: Earnings Call & Narrative Analysis Engine
- [ ] **Phase 3**: Agent Memory & State Management
- [ ] **Phase 4**: Multi-Source Synthesis & Reasoning Pipeline
- [ ] **Phase 5**: Report Generation & Delivery Interface
- [ ] **Phase 6**: Financial Evaluation & Benchmark Suite

## 📄 License

MIT License - see `LICENSE` for details.
