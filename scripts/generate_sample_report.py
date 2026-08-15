"""Script to generate sample portfolio research report in Markdown and PDF format."""

from agent.synthesis.engine import SynthesisResult, ConsolidatedClaim
from agent.synthesis.conflict_resolution import EvidenceItem, Conflict
from agent.reporting.builder import ReportBuilder

def main():
    item_sec = EvidenceItem(
        id="e1",
        text="FY2024 Total Revenue reached $158.0B, representing 6.7% YoY growth.",
        source="SEC EDGAR 10-K FY2024",
        source_type="sec_filing"
    )
    item_transcript = EvidenceItem(
        id="e2",
        text="Q4 Net Interest Margin expanded to 2.75% with strong credit quality.",
        source="Q4 2024 Earnings Call",
        source_type="earnings_transcript"
    )
    item_unverified = EvidenceItem(
        id="e3",
        text="Blog claims FY2024 revenue was $140.0B.",
        source="Third-Party Post",
        source_type="agent_note"
    )

    conflict = Conflict(
        topic="FY2024 Revenue",
        evidence_a=item_sec,
        evidence_b=item_unverified,
        discrepancy="Metric Revenue discrepancy (12.0% variance): SEC 10-K ($158.0B) vs Blog ($140.0B).",
        resolved=True,
        winning_evidence_id="e1",
        resolution_strategy="Hierarchical Source Weight & Recency Preference",
        reasoning="Resolved in favor of SEC 10-K filing due to statutory authority (weight 1.0 vs 0.70)."
    )

    synthesis = SynthesisResult(
        summary_narrative="JPMorgan Chase & Co. (JPM) delivered outstanding FY2024 financial performance, characterized by robust revenue expansion to $158.0B and disciplined risk management. CET1 capital ratio stands strong at 14.2%.",
        consolidated_claims=[
            ConsolidatedClaim(
                claim_id="c1",
                statement="FY2024 Total Revenue reached $158.0B (6.7% YoY growth).",
                supporting_evidence_ids=["e1"],
                citations=["SEC EDGAR 10-K FY2024"],
                confidence_score=1.0
            ),
            ConsolidatedClaim(
                claim_id="c2",
                statement="Net Interest Margin expanded to 2.75% with CET1 ratio at 14.2%.",
                supporting_evidence_ids=["e2"],
                citations=["Q4 2024 Earnings Call Transcript"],
                confidence_score=0.85
            )
        ],
        conflicts_found=[conflict],
        overall_confidence=0.95
    )

    fin_data = {
        "entity_name": "JPMorgan Chase & Co.",
        "metrics": {
            "Revenues": [
                {"fy": 2024, "form": "10-K", "val": 158000000000, "filed": "2025-02-15"},
                {"fy": 2023, "form": "10-K", "val": 148000000000, "filed": "2024-02-16"}
            ],
            "NetIncomeLoss": [
                {"fy": 2024, "form": "10-K", "val": 57000000000, "filed": "2025-02-15"},
                {"fy": 2023, "form": "10-K", "val": 49000000000, "filed": "2024-02-16"}
            ],
            "Assets": [
                {"fy": 2024, "form": "10-K", "val": 3875000000000, "filed": "2025-02-15"}
            ],
            "Liabilities": [
                {"fy": 2024, "form": "10-K", "val": 3520000000000, "filed": "2025-02-15"}
            ],
            "StockholdersEquity": [
                {"fy": 2024, "form": "10-K", "val": 355000000000, "filed": "2025-02-15"}
            ]
        }
    }

    builder = ReportBuilder()
    report = builder.build(
        synthesis_result=synthesis,
        financial_data=fin_data,
        company_name="JPMorgan Chase & Co.",
        ticker="JPM"
    )

    saved = report.save(
        markdown_path="examples/sample_research_report.md",
        pdf_path="examples/sample_research_report.pdf"
    )
    print("Successfully generated sample demonstration reports:", saved)

if __name__ == "__main__":
    main()
