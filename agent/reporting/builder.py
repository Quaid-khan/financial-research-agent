"""Phase 5: Report Builder & Document Generation Engine.

Transforms Phase 4 SynthesisResult and structured financial statement data into
publication-grade financial research reports formatted as Markdown and exported as PDF.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

from agent.synthesis.engine import SynthesisResult
from agent.reporting.templates.markdown_template import render_markdown_report

logger = logging.getLogger("financial_agent.reporting")


class PDFReportGenerator(FPDF if HAS_FPDF else object):
    """Custom FPDF2 canvas for generating styled institutional financial PDFs."""

    def __init__(self, title_text: str = "Financial Research Report"):
        if not HAS_FPDF:
            raise RuntimeError("fpdf2 package is required for PDF export. Run 'pip install fpdf2'.")
        super().__init__(orientation="P", unit="mm", format="A4")
        self.title_text = title_text
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 110, 120)
        self.cell(0, 8, "ANTIGRAVITY AUTONOMOUS FINANCIAL RESEARCH", border=False, new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_draw_color(200, 210, 220)
        self.line(10, 16, 200, 16)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()} | Institutional Disclosures & Citation Verified", align="C")


class Report:
    """Container holding synthesized research report in Markdown and PDF export utility."""

    def __init__(
        self,
        markdown_content: str,
        company_name: str,
        ticker: str,
        synthesis_result: SynthesisResult
    ):
        self.markdown_content = markdown_content
        self.company_name = company_name
        self.ticker = ticker
        self.synthesis_result = synthesis_result

    def to_markdown(self) -> str:
        return self.markdown_content

    def to_pdf(self, output_path: str) -> str:
        """Export report as a formatted PDF file at output_path.
        
        Returns:
            Absolute path to written PDF file.
        """
        path_obj = Path(output_path).resolve()
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        pdf = PDFReportGenerator(title_text=f"Research Report: {self.company_name} ({self.ticker.upper()})")
        pdf.add_page()
        pdf.set_font("Helvetica", size=10)

        # Parse markdown lines into styled PDF elements
        for line in self.markdown_content.split("\n"):
            line_str = line.strip()
            if not line_str:
                pdf.ln(3)
                continue

            # 1. Replace common Unicode typography characters with ASCII equivalents
            clean_text = (
                line_str.replace("•", "- ")
                .replace("—", "- ")
                .replace("–", "- ")
                .replace("“", '"')
                .replace("”", '"')
                .replace("’", "'")
                .replace("‘", "'")
                .replace("**", "")
                .replace("`", "")
                .replace("*", "")
            )
            # 2. Strict ASCII encoding to guarantee FPDF Helvetica core font compatibility
            clean_text = clean_text.encode("ascii", errors="ignore").decode("ascii")

            if not clean_text:
                continue

            if clean_text.startswith("# "):
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(20, 40, 80)
                pdf.multi_cell(0, 8, clean_text[2:])
                pdf.ln(2)
            elif clean_text.startswith("## "):
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(30, 60, 110)
                pdf.multi_cell(0, 7, clean_text[3:])
                pdf.ln(2)
            elif clean_text.startswith("### "):
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(0, 6, clean_text[4:])
                pdf.ln(1)
            elif clean_text.startswith("|"):
                pdf.set_font("Courier", size=8)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 5, clean_text[:90], new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", size=9)
                pdf.set_text_color(20, 20, 20)
                pdf.multi_cell(0, 5, clean_text)
                pdf.ln(1)

        pdf.output(str(path_obj))
        logger.info(f"Generated PDF report at '{path_obj}'.")
        return str(path_obj)

    def save(self, markdown_path: Optional[str] = None, pdf_path: Optional[str] = None) -> Dict[str, str]:
        """Save report to Markdown and/or PDF file paths."""
        saved_paths = {}
        if markdown_path:
            m_path = Path(markdown_path).resolve()
            m_path.parent.mkdir(parents=True, exist_ok=True)
            m_path.write_text(self.markdown_content, encoding="utf-8")
            saved_paths["markdown"] = str(m_path)

        if pdf_path:
            pdf_out = self.to_pdf(pdf_path)
            saved_paths["pdf"] = pdf_out

        return saved_paths


class ReportBuilder:
    """Builder engine orchestrating synthesis results & templates into Report objects."""

    def build(
        self,
        synthesis_result: SynthesisResult,
        financial_data: Optional[Dict[str, Any]] = None,
        company_name: str = "JPMorgan Chase & Co.",
        ticker: str = "JPM",
        use_llm: bool = True
    ) -> Report:
        """Build institutional Report object."""
        markdown_text = render_markdown_report(
            company_name=company_name,
            ticker=ticker,
            synthesis_result=synthesis_result,
            financial_data=financial_data
        )

        return Report(
            markdown_content=markdown_text,
            company_name=company_name,
            ticker=ticker.upper(),
            synthesis_result=synthesis_result
        )
