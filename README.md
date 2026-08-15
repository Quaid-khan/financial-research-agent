# Autonomous Financial Research Agent for BFSI

An autonomous, multi-tool AI agent system designed for Banking, Financial Services, and Insurance (BFSI) use cases. Powered by Google Gemini (`gemini-3.6-flash`), this agent conducts deep financial research across SEC filings (10-K, 10-Q), earnings call transcripts, market data, and regulatory disclosures to produce synthesized, publication-grade financial analysis reports.

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
│   ├── core.py        # ReAct control loop, AgentState, AgentStep, ToolCall
│   ├── config.py      # Environment validation & Pydantic settings schema
│   ├── tools/
│   │   └── registry.py# ToolRegistry, ToolDefinition, FunctionDeclaration export
│   ├── memory/        # Episodic, semantic, and working memory stores
│   ├── synthesis/     # Multi-source intelligence & reconciliation engines
│   └── reporting/     # Structured research report generators & formatters
├── eval/
│   └── challenges/    # Benchmark evaluation cases and financial test suites
├── scripts/
│   └── check_setup.py # System setup & environment verification script
├── tests/
│   ├── test_config.py     # Config validation unit tests
│   └── test_react_loop.py # ReAct loop & ToolRegistry unit tests
├── examples/
│   └── demo_agent.py  # CLI harness demo testing agent against stub tools
├── cache/             # Local data and document cache
├── .env.example       # Environment configuration template
├── CHANGELOG.md       # Version history and phase progression tracking
├── requirements.txt   # Project dependencies
└── README.md          # Project overview & documentation
```

## 🛠️ Tech Stack & Conventions

- **Language**: Python 3.11+
- **LLM Engine**: Google Gemini API (`gemini-3.6-flash`) via `google-genai`
- **Control Flow**: ReAct (Reason-Act-Observe) pattern with structured scratchpad tracing
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

## 📜 Roadmap & Build Phases

- [x] **Phase 0**: Project Setup & Environment Configuration Engine
- [x] **Phase 1**: ReAct Core Engine & Tool Registry Architecture
- [ ] **Phase 2**: SEC EDGAR Filing Retrieval & Financial Ratio Tools
- [ ] **Phase 3**: Earnings Call & Narrative Analysis Engine
- [ ] **Phase 4**: Agent Memory & State Management
- [ ] **Phase 5**: Multi-Source Synthesis & Reasoning Pipeline
- [ ] **Phase 6**: Report Generation & Delivery Interface
- [ ] **Phase 7**: Financial Evaluation & Benchmark Suite

## 📄 License

MIT License - see `LICENSE` for details.
