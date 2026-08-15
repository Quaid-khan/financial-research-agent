# Autonomous Financial Research Agent for BFSI

An autonomous, multi-tool AI agent system designed for Banking, Financial Services, and Insurance (BFSI) use cases. Powered by Google Gemini (`gemini-3.6-flash`), this agent conducts deep financial research across SEC filings (10-K, 10-Q), earnings call transcripts, market data, and regulatory disclosures to produce synthesized, publication-grade financial analysis reports.

## 🎯 Key Objectives & Capabilities

- **Interactive Web Dashboard**: Full-featured institutional Web UI (`http://127.0.0.1:5000`) for running agent queries, streaming live ReAct traces, viewing financial statement tables, downloading PDF/Markdown reports, and inspecting evaluation scorecards.
- **SEC Filings Analysis**: Extraction, parsing, and financial ratio analysis from SEC EDGAR 10-K, 10-Q, and 8-K disclosures.
- **Earnings Transcript Processing**: Qualitative sentiment tracking, executive guidance extraction, and Q&A topic breakdown.
- **Three-Layer Memory System**: Working (short-term), Episodic (session-term), and Long-Term (cross-session ChromaDB vector store with hybrid scoring).
- **Multi-Source Synthesis & Conflict Resolution**: Automated numerical/narrative discrepancy detection with explicit surfacing and source reliability weighting.
- **Publication-Grade Report Generation**: Generating standardized Markdown and PDF reports with auto-rendered XBRL financial tables, inline source citations, and conflict transparency.
- **21-Metric Financial Evaluation Framework**: Systematic scoring suite across 7 categories (Factual Accuracy, Completeness, Reasoning Quality, Conflict Handling, Memory Utilization, Report Quality, Efficiency & Budget).
- **8 End-to-End Benchmark Challenges**: Automated benchmark suite validating complete agent capabilities from simple lookups to capstone research reports (100% Pass Rate).

## 🖥️ Interactive Web UI Dashboard

The system includes an interactive web dashboard interface. Launch the server and open your web browser at:

👉 **`http://127.0.0.1:5000`**

### Features:
- **Live ReAct Execution Trace**: Inspect reasoning thoughts, tool invocations, and observations step-by-step.
- **Institutional Research Reports**: Preview Markdown reports and download clean PDF reports with 1 click.
- **21-Metric Scorecard Viewer**: Interactively inspect overall score, letter grade (`A+` to `F`), and individual metric breakdowns.
- **Portfolio Downloads**: Access pre-generated demonstration reports and scorecards.

```bash
# Launch Web Dashboard Server
python web/app.py
```

---

## 🏗️ Project Architecture

```
financial-research-agent/
├── web/
│   ├── app.py         # HTTP Web Dashboard Server & REST API endpoints
│   └── static/        # Web UI HTML, CSS styles, and JavaScript client logic
├── agent/
│   ├── core.py        # ReAct control loop, AgentState, AgentStep, ToolCall
│   ├── config.py      # Environment validation & Pydantic settings schema
│   ├── tools/
│   │   ├── registry.py    # ToolRegistry, ToolDefinition, FunctionDeclaration export
│   │   ├── cache.py       # SQLite response caching engine (LocalCache)
│   │   ├── edgar.py       # SEC EDGAR search, section parser, XBRL company facts
│   │   └── transcripts.py # Earnings call transcript fetcher & Q&A segmenter
│   ├── memory/
│   │   ├── working.py  # Short-term context & token budget window manager
│   │   ├── episodic.py # Session-term subtask logger & finding recall
│   │   └── longterm.py # Persistent ChromaDB vector store & hybrid scoring
│   ├── synthesis/
│   │   ├── engine.py              # SynthesisEngine & SynthesisResult generator
│   │   └── conflict_resolution.py # ConflictDetector, EvidenceItem & resolution policy
│   └── reporting/
│       ├── builder.py   # ReportBuilder and Report container (to_markdown, to_pdf)
│       └── templates/   # Markdown and financial table template renderers
├── eval/
│   ├── metrics.py               # 21 named evaluation metric functions across 7 categories
│   ├── evaluator.py             # Evaluator orchestrator executing agent trace evaluation
│   ├── scorecard.py             # Scorecard model with overall score (0-100), grade (A+-F), & formatters
│   ├── run_all_challenges.py    # Benchmark runner executing all 8 end-to-end challenges
│   └── challenges/              # 8 End-to-End Benchmark Challenges (challenge_01 - challenge_08)
├── scripts/
│   ├── check_setup.py               # System setup & environment verification script
│   ├── generate_sample_report.py    # Sample research report generation script
│   └── generate_sample_scorecard.py # Sample evaluation scorecard generation script
├── tests/
│   ├── test_config.py      # Config validation unit tests
│   ├── test_react_loop.py  # ReAct loop & ToolRegistry unit tests
│   ├── test_edgar_tools.py # SEC EDGAR tools unit tests (mocked fixtures)
│   ├── test_transcripts.py # Earnings transcripts tools unit tests
│   ├── test_memory.py      # Three-layer memory system unit tests
│   ├── test_synthesis.py   # Multi-source synthesis & conflict resolution unit tests
│   ├── test_reporting.py   # ReportBuilder, table rendering & PDF export unit tests
│   ├── test_eval.py        # 21 evaluation metrics, Evaluator & Scorecard unit tests
│   └── test_challenges.py  # 8 End-to-end benchmark challenge unit tests
├── examples/
│   ├── demo_agent.py             # CLI harness demo testing agent against registered tools
│   ├── sample_research_report.md  # Sample portfolio demonstration report (Markdown)
│   ├── sample_research_report.pdf # Sample portfolio demonstration report (PDF)
│   ├── sample_scorecard.json      # Sample evaluation scorecard output (JSON)
│   └── sample_scorecard.md        # Sample evaluation scorecard summary (Markdown)
├── RESULTS.md         # Portfolio centerpiece benchmark results matrix (100% Pass Rate)
├── cache/             # Local SQLite database and ChromaDB persistent storage
├── .env.example       # Environment configuration template
├── CHANGELOG.md       # Version history and phase progression tracking
├── requirements.txt   # Project dependencies
└── README.md          # Project overview & documentation
```

## 🛠️ Tech Stack & Conventions

- **Language**: Python 3.11+
- **LLM Engine**: Google Gemini API (`gemini-3.6-flash`) via `google-genai`
- **Frontend / Web UI**: HTML5, Vanilla CSS3, Client JavaScript, REST APIs
- **Control Flow**: ReAct (Reason-Act-Observe) pattern with structured scratchpad tracing
- **Data Tools**: SEC EDGAR API (10-K/10-Q/XBRL facts) + Earnings Call Transcripts
- **Report Generation**: Markdown & PDF export (`fpdf2`) with auto-generated financial tables
- **Synthesis Engine**: Multi-source claim consolidation & explicit conflict resolution
- **Memory Architecture**: 3-Layer (Working, Episodic, Long-Term ChromaDB with Hybrid Scoring)
- **Evaluation Suite**: 21 named metrics across 7 categories producing institutional scorecards
- **Benchmark Suite**: 8 end-to-end challenges validating capabilities across all phases
- **Data Models**: Pydantic v2 for strict type safety and schema validation
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Vector DB**: ChromaDB (`./cache/chroma_db`)
- **Testing**: Pytest unit test coverage (45 passing tests)

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

2. **Activate Virtual Environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify System Setup**:
   ```bash
   python scripts/check_setup.py
   ```

5. **Launch Interactive Web UI Dashboard**:
   ```bash
   python web/app.py
   ```
   Open **`http://127.0.0.1:5000`** in your web browser.

6. **Run 8 Benchmark Challenges**:
   ```bash
   python -m eval.run_all_challenges
   ```

7. **Generate Sample Research Report**:
   ```bash
   python -m scripts.generate_sample_report
   ```

8. **Generate Sample Evaluation Scorecard**:
   ```bash
   python -m scripts.generate_sample_scorecard
   ```

9. **Run Complete Unit Test Suite**:
   ```bash
   pytest tests/
   ```

## 📜 Roadmap & Build Phases

- [x] **Phase 0**: Project Setup & Environment Configuration Engine
- [x] **Phase 1**: ReAct Core Engine & Tool Registry Architecture
- [x] **Phase 2**: SEC EDGAR Filing Retrieval & Financial Ratio Tools
- [x] **Phase 3**: Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- [x] **Phase 4**: Multi-Source Synthesis Engine & Explicit Conflict Resolution
- [x] **Phase 5**: Publication-Grade Report Generation & PDF Delivery Engine
- [x] **Phase 6**: Financial Evaluation Framework (21 Metrics across 7 Categories)
- [x] **Phase 7**: End-to-End Benchmark Challenges & Web Dashboard UI (100% Pass Rate)

## 📄 License

MIT License - see `LICENSE` for details.
