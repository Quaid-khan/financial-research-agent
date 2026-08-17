"""Hugging Face Space & Standard Entrypoint for QK Researcher."""
import os
import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web.app import run_web_server, execute_research_pipeline

# Try importing gradio if running on Hugging Face Gradio SDK
try:
    import gradio as gr
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

if HAS_GRADIO:
    # Start background HTTP web server on port 8050
    t = threading.Thread(target=run_web_server, args=(8050,), daemon=True)
    t.start()

    def research_fn(ticker: str, task: str):
        try:
            report_data, scorecard_data, state_data = execute_research_pipeline(ticker, task)
            return report_data.get("markdown_content", "Research brief generated.")
        except Exception as err:
            return f"Error executing research task: {err}"

    with gr.Blocks(title="QK Researcher - Autonomous Financial Intelligence") as demo:
        gr.Markdown("# 📊 QK Researcher — Autonomous Financial Intelligence Engine")
        gr.Markdown("### Primary Statutory 10-K Lineage Verification, Multi-Market Routing & DCF Valuation")
        
        with gr.Row():
            ticker_input = gr.Textbox(label="Stock Ticker / Entity Symbol", value="JPM", placeholder="e.g. JPM, AAPL, AMZN, NBP, HBL")
            task_input = gr.Textbox(label="Research Task Prompt", value="Analyze revenue, net income, total assets, and capital ratios for the last 3 fiscal years.")
        
        btn = gr.Button("🚀 Generate Financial Research Brief", variant="primary")
        output = gr.Markdown(label="Synthesized Financial Research Brief")
        
        btn.click(fn=research_fn, inputs=[ticker_input, task_input], outputs=output)

    demo.launch()
else:
    port = int(os.environ.get("PORT", 8050))
    print(f"Starting QK Researcher Web Server on port {port}...")
    run_web_server(port=port)
