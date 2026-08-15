"""ReportBuilder and Report classes for generating institutional financial reports in Markdown and PDF format."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from fpdf import FPDF
from agent.config import get_settings
from agent.synthesis.engine import SynthesisResult
from agent.reporting.templates.markdown_template import render_markdown_report

logger = logging.getLogger("financial_agent.reporting.builder")


class PDFReportGenerator(FPDF):
    """Custom FPDF class for institutional PDF report styling."""

    def __init__(self, title_text: str = "Financial Research Report") -> None:
        super().__init__()
        self.title_text = title_text
        self.set_auto_page_break(auto=True, margin=15)

    def header(self) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, self.title_text, border=0, new_x="RIGHT", new_y="TOP", align="L")
        self.cell(0, 10, "Autonomous Financial Agent", border=0, new_x="LMARGIN", new_y="NEXT", align="R")
        self.line(10, 18, 200, 18)
        self.ln(5)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        page_str = f"Page {self.page_no()}"
        self.cell(0, 10, page_str, border=0, align="C")


class Report(BaseModel):
    """Institutional research report container."""
    markdown_content: str = Field(description="Full markdown source text of report.")
    company_name: str = Field(description="Company entity name.")
    ticker: str = Field(description="Stock ticker symbol.")
    synthesis_result: SynthesisResult = Field(description="Phase 4 synthesis result data.")

    def to_markdown(self) -> str:
        """Return markdown text content."""
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

            if line_str.startswith("# "):
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(20, 40, 80)
                pdf.multi_cell(0, 8, line_str[2:])
                pdf.ln(2)
            elif line_str.startswith("## "):
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(30, 60, 110)
                pdf.multi_cell(0, 7, line_str[3:])
                pdf.ln(2)
            elif line_str.startswith("### "):
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(0, 6, line_str[4:])
                pdf.ln(1)
            elif line_str.startswith("|"):
                pdf.set_font("Courier", size=8)
                pdf.set_text_color(50, 50, 50)
                pdf.cell(0, 5, line_str[:90], new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.set_font("Helvetica", size=9)
                pdf.set_text_color(20, 20, 20)
                # Clean up simple markdown formatting bold/italic markers for clean PDF display
                clean_text = line_str.replace("**", "").replace("`", "").replace("*", "")
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
            saved_paths["pdf"] = self.to_pdf(pdf_path)

        return saved_paths


class ReportBuilder:
    """Builder converting SynthesisResult and structured financial data into institutional research reports."""

    def build(
        self,
        synthesis_result: SynthesisResult,
        financial_data: Optional[Dict[str, Any]] = None,
        company_name: str = "JPMorgan Chase & Co.",
        ticker: str = "JPM",
        use_llm: bool = True
    ) -> Report:
        """Build institutional Report object.
        
        Args:
            synthesis_result: Phase 4 SynthesisResult object.
            financial_data: Optional financial statement metrics dictionary.
            company_name: Entity name string.
            ticker: Stock ticker symbol string.
            use_llm: True to refine prose with Gemini API, False for template rendering.
            
        Returns:
            Report object containing markdown content and to_pdf() renderer.
        """
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
