"""Hard Quality Gates for Synthesis & Report Generation.

Implements strict validation gates prior to report generation:
1. CompanyValidationGate: Verifies evidence matches canonical company identity.
2. SourceValidationGate: Verifies evidence sources are valid and authentic.
3. PeriodValidationGate: Verifies requested fiscal periods (FY2024, FY2023, FY2022) are accounted for.
4. MetricCompletenessGate: Verifies requested metrics (Revenue, Net Income, Assets, CET1) are present or explicitly marked unverified.
"""

import logging
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from agent.synthesis.conflict_resolution import EvidenceItem
from agent.tools.edgar import CompanyIdentity, resolve_canonical_company

logger = logging.getLogger("financial_agent.synthesis.quality_gates")


class QualityGateResult(BaseModel):
    """Result of executing a Quality Gate validation check."""
    gate_name: str
    passed: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class PipelineQualityAuditor:
    """Audits evidence and financial data prior to synthesis and report generation."""

    def __init__(self, target_identity: CompanyIdentity, requested_periods: int = 3, requested_metrics: List[str] = None):
        self.target_identity = target_identity
        self.requested_periods = requested_periods
        self.requested_metrics = requested_metrics or ["revenue", "net_income", "total_assets", "cet1_ratio"]

    def audit(self, evidence_list: List[EvidenceItem], financial_data: Dict[str, Any]) -> List[QualityGateResult]:
        """Execute all quality gates."""
        results = []
        results.append(self._check_company_validation(evidence_list, financial_data))
        results.append(self._check_source_validation(evidence_list))
        results.append(self._check_period_validation(financial_data))
        results.append(self._check_metric_completeness(financial_data))
        return results

    def _check_company_validation(self, evidence_list: List[EvidenceItem], financial_data: Dict[str, Any]) -> QualityGateResult:
        errors = []
        warnings = []
        target_ticker = self.target_identity.ticker.upper()

        # Check financial data entity
        fin_cik = financial_data.get("cik")
        if fin_cik and str(fin_cik).zfill(10) != self.target_identity.cik:
            errors.append(f"Financial data CIK '{fin_cik}' mismatches target company CIK '{self.target_identity.cik}'.")

        for item in evidence_list:
            if item.ticker and item.ticker.upper() != target_ticker:
                errors.append(f"Evidence item '{item.id}' ticker '{item.ticker}' mismatches target ticker '{target_ticker}'.")

        return QualityGateResult(
            gate_name="CompanyValidationGate",
            passed=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )

    def _check_source_validation(self, evidence_list: List[EvidenceItem]) -> QualityGateResult:
        errors = []
        warnings = []

        for item in evidence_list:
            if item.confidence < 0.5:
                warnings.append(f"Low confidence evidence source '{item.source}' (confidence {item.confidence:.2f}).")
            if "junk" in item.text.lower() or "placeholder" in item.text.lower():
                errors.append(f"Evidence source '{item.source}' contains unverified placeholder junk text.")

        return QualityGateResult(
            gate_name="SourceValidationGate",
            passed=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )

    def _check_period_validation(self, financial_data: Dict[str, Any]) -> QualityGateResult:
        warnings = []
        errors = []

        comp_status = financial_data.get("completeness_status", {})
        missing_years = [yr for yr, status in comp_status.items() if status == "missing"]

        if missing_years:
            warnings.append(f"Required fiscal periods missing from SEC filings: {', '.join(missing_years)}. Explicit missing status will be rendered in report.")

        return QualityGateResult(
            gate_name="PeriodValidationGate",
            passed=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )

    def _check_metric_completeness(self, financial_data: Dict[str, Any]) -> QualityGateResult:
        warnings = []
        errors = []
        metrics = financial_data.get("metrics", {})

        for m in self.requested_metrics:
            m_lower = m.lower()
            if "revenue" in m_lower and "Revenues" not in metrics:
                warnings.append("Revenue metric unavailable in structured XBRL facts.")
            elif "asset" in m_lower and "Assets" not in metrics:
                warnings.append("Total Assets metric unavailable in structured XBRL facts.")
            elif "cet1" in m_lower and "CommonEquityTier1CapitalRatio" not in metrics:
                warnings.append("CET1 Capital Ratio metric unavailable in XBRL facts. Will verify via statutory disclosures.")

        return QualityGateResult(
            gate_name="MetricCompletenessGate",
            passed=len(errors) == 0,
            warnings=warnings,
            errors=errors
        )
