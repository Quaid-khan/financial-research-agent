"""Phase 6: 21-Metric Quantitative Evaluation Framework & Scorecard Generator.

Evaluates synthesized research report and agent execution trace across 7 core categories:
1. Factual Accuracy
2. Completeness
3. Reasoning Quality
4. Conflict Handling
5. Memory Utilization
6. Report Quality
7. Efficiency & Budget
"""

import logging
from typing import Dict, Any, List

from agent.core import AgentState
from agent.reporting.builder import Report
from eval.scorecard import Scorecard, compute_grade
from eval.metrics import (
    MetricResult,
    metric_citation_coverage,
    metric_citation_correctness,
    metric_numeric_accuracy,
    metric_section_completeness,
    metric_financial_depth,
    metric_source_breadth,
    metric_react_efficiency,
    metric_tool_selection_appropriateness,
    metric_error_recovery_rate,
    metric_conflict_detection_rate,
    metric_conflict_transparency,
    metric_working_memory_efficiency,
    metric_episodic_recall_accuracy,
    metric_longterm_memory_hit_rate,
    metric_readability_score,
    metric_professional_tone,
    metric_formatting_correctness,
    metric_token_efficiency,
    metric_execution_latency,
    metric_api_call_efficiency,
    metric_cost_estimate
)

logger = logging.getLogger("financial_agent.eval.evaluator")


class Evaluator:
    """Orchestrator class running 21 evaluation metrics across 7 core categories."""

    def evaluate(
        self,
        state: AgentState,
        report: Report,
        duration_seconds: float = 5.0
    ) -> Scorecard:
        """Run complete evaluation metrics suite on agent execution state and generated report."""
        logger.info(f"Starting agent evaluation for task: '{state.task}'")

        # Execute all 21 metric functions
        metrics: List[MetricResult] = [
            # Category 1: Factual Accuracy
            metric_citation_coverage(report),
            metric_citation_correctness(report),
            metric_numeric_accuracy(report),
            
            # Category 2: Completeness
            metric_section_completeness(report),
            metric_financial_depth(report),
            metric_source_breadth(report),

            # Category 3: Reasoning Quality
            metric_react_efficiency(state),
            metric_tool_selection_appropriateness(state),
            metric_error_recovery_rate(state),

            # Category 4: Conflict Handling
            metric_conflict_detection_rate(report),
            metric_conflict_transparency(report),

            # Category 5: Memory Utilization
            metric_working_memory_efficiency(state),
            metric_episodic_recall_accuracy(state),
            metric_longterm_memory_hit_rate(state),

            # Category 6: Report Quality
            metric_readability_score(report),
            metric_professional_tone(report),
            metric_formatting_correctness(report),

            # Category 7: Efficiency & Budget
            metric_token_efficiency(state),
            metric_execution_latency(duration_seconds),
            metric_api_call_efficiency(state),
            metric_cost_estimate(state)
        ]

        # Apply execution failure penalty if agent trace failed to complete task
        is_completed = getattr(state, "is_completed", True)
        if not is_completed:
            for idx, m in enumerate(metrics):
                if m.category in ["Reasoning Quality", "Factual Accuracy", "Completeness"]:
                    metrics[idx] = MetricResult(
                        metric_name=m.metric_name,
                        category=m.category,
                        score=min(m.score, 30.0),
                        description=f"Penalized due to incomplete/failed execution state: {m.description}"
                    )

        # Compute Category Scores
        cat_map: Dict[str, List[float]] = {}
        for m in metrics:
            cat_map.setdefault(m.category, []).append(m.score)

        category_scores = {cat: round(sum(scores) / len(scores), 2) for cat, scores in cat_map.items()}

        # Compute Overall Score
        overall_score = round(sum(category_scores.values()) / len(category_scores), 2)
        grade = compute_grade(overall_score)

        # Generate Actionable Recommendations
        recommendations = []
        for m in metrics:
            if m.score < 85.0:
                recommendations.append(f"Improve `{m.metric_name}` (Score: {m.score:.1f}/100): {m.description}")

        if not recommendations:
            recommendations.append("Outstanding research quality across all 21 evaluation metrics!")

        scorecard = Scorecard(
            overall_score=overall_score,
            grade=grade,
            category_scores=category_scores,
            metric_results=metrics,
            recommendations=recommendations
        )

        logger.info(f"Finished evaluation. Overall Score: {overall_score:.2f}/100.0 (Grade: {grade})")
        return scorecard
