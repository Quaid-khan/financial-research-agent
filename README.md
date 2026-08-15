# Autonomous Financial Research Agent for BFSI

An autonomous, multi-tool AI agent system designed for Banking, Financial Services, and Insurance (BFSI) use cases. Powered by Google Gemini (`gemini-3.6-flash`), this agent conducts deep financial research across SEC filings (10-K, 10-Q), earnings call transcripts, market data, and regulatory disclosures to produce synthesized, publication-grade financial analysis reports.

## 🎯 Key Objectives & Capabilities

- **SEC Filings Analysis**: Extraction, parsing, and financial ratio analysis from SEC EDGAR 10-K, 10-Q, and 8-K disclosures.
- **Earnings Transcript Processing**: Qualitative sentiment tracking, executive guidance extraction, and Q&A topic breakdown.
- **Three-Layer Memory System**: Working (short-term), Episodic (session-term), and Long-Term (cross-session ChromaDB vector store with hybrid scoring).
- **Multi-Source Synthesis**: Cross-referencing quantitative financial metrics with qualitative disclosure narrative and macroeconomic data.
- **Structured Report Generation**: Generating standardized institutional research notes, risk matrices, and valuation context summaries.
- **Rigorous Evaluation Suite**: Domain-specific evaluation framework designed to score factual precision, numeric accuracy, hallucination resistance, and analytical depth.

## 🏗️ Project Architecture

```
financial-research-agent/
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
│   ├── synthesis/     # Multi-source intelligence & reconciliation engines
│   └── reporting/     # Structured research report generators & formatters
├── eval/
│   └── challenges/    # Benchmark evaluation cases and financial test suites
├── scripts/
│   └── check_setup.py # System setup & environment verification script
├── tests/
│   ├── test_config.py      # Config validation unit tests
│   ├── test_react_loop.py  # ReAct loop & ToolRegistry unit tests
│   ├── test_edgar_tools.py # SEC EDGAR tools unit tests (mocked fixtures)
│   ├── test_transcripts.py # Earnings transcripts tools unit tests
│   └── test_memory.py      # Three-layer memory system unit tests
├── examples/
│   └── demo_agent.py  # CLI harness demo testing agent against registered tools
├── cache/             # Local SQLite database and ChromaDB persistent storage
├── .env.example       # Environment configuration template
├── CHANGELOG.md       # Version history and phase progression tracking
├── requirements.txt   # Project dependencies
└── README.md          # Project overview & documentation
```

## 🛠️ Tech Stack & Conventions

- **Language**: Python 3.11+
- **LLM Engine**: Google Gemini API (`gemini-3.6-flash`) via `google-genai`
- **Control Flow**: ReAct (Reason-Act-Observe) pattern with structured scratchpad tracing
- **Data Tools**: SEC EDGAR API (10-K/10-Q/XBRL facts) + Earnings Call Transcripts
- **Memory Architecture**: 3-Layer (Working, Episodic, Long-Term ChromaDB with Hybrid Scoring)
- **Data Models**: Pydantic v2 for strict type safety and schema validation
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Vector DB**: ChromaDB (`./cache/chroma_db`)
- **Testing**: Pytest unit test coverage (25 passing tests)
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

5. **Run ReAct Agent Demo Harness**:
   ```bash
   python examples/demo_agent.py
   ```

6. **Run Unit Tests**:
   ```bash
   pytest tests/
   ```

## 📜 Roadmap & Build Phases

- [x] **Phase 0**: Project Setup & Environment Configuration Engine
- [x] **Phase 1**: ReAct Core Engine & Tool Registry Architecture
- [x] **Phase 2**: SEC EDGAR Filing Retrieval & Financial Ratio Tools
- [x] **Phase 3**: Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- [ ] **Phase 4**: Earnings Call & Narrative Analysis Engine
- [ ] **Phase 5**: Multi-Source Synthesis & Reasoning Pipeline
- [ ] **Phase 6**: Report Generation & Delivery Interface
- [ ] **Phase 7**: Financial Evaluation & Benchmark Suite

## 📄 License

MIT License - see `LICENSE` for details.
