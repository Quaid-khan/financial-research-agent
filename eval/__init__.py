"""Evaluation Framework Package for Financial Agent.

Exports Evaluator, Scorecard, and MetricResult.
"""

from eval.metrics import MetricResult
from eval.scorecard import Scorecard
from eval.evaluator import Evaluator

__all__ = [
    "Evaluator",
    "Scorecard",
    "MetricResult",
]
