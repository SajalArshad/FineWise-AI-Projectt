"""
financial_calculator.py
------------------------
Pure, deterministic Python math. No AI/LLM calls live here.
Given the same inputs, these functions always return the same outputs.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class FinancialCalculation:
    monthly_income: float
    expenses: Dict[str, float]
    savings: float
    total_expenses: float = field(init=False)
    remaining_income: float = field(init=False)
    savings_ratio: float = field(init=False)
    expense_ratio: float = field(init=False)
    debt_ratio: float = field(init=False)
    preliminary_score: int = field(init=False)

    def __post_init__(self):
        self.total_expenses = calculate_total_expenses(self.expenses)
        self.remaining_income = calculate_remaining_income(
            self.monthly_income, self.total_expenses
        )
        self.savings_ratio = calculate_savings_ratio(
            self.savings, self.monthly_income
        )
        self.expense_ratio = calculate_expense_ratio(
            self.total_expenses, self.monthly_income
        )
        debt = self.expenses.get("loan_debt", 0)
        self.debt_ratio = calculate_expense_ratio(debt, self.monthly_income)
        self.preliminary_score = calculate_preliminary_score(
            savings_ratio=self.savings_ratio,
            remaining_income=self.remaining_income,
            expense_ratio=self.expense_ratio,
            debt_ratio=self.debt_ratio,
        )

    def to_dict(self) -> dict:
        return {
            "monthly_income": self.monthly_income,
            "expenses": self.expenses,
            "savings": self.savings,
            "total_expenses": round(self.total_expenses, 2),
            "remaining_income": round(self.remaining_income, 2),
            "savings_ratio": round(self.savings_ratio, 2),
            "expense_ratio": round(self.expense_ratio, 2),
            "debt_ratio": round(self.debt_ratio, 2),
            "preliminary_score": self.preliminary_score,
        }


def calculate_total_expenses(expenses: Dict[str, float]) -> float:
    """Sum of all expense categories."""
    return float(sum(expenses.values()))


def calculate_remaining_income(monthly_income: float, total_expenses: float) -> float:
    """Income left after all expenses (can be negative)."""
    return float(monthly_income) - float(total_expenses)


def _safe_divide(numerator: float, denominator: float) -> float:
    """Guard against divide-by-zero when income is 0."""
    if not denominator:
        return 0.0
    return numerator / denominator


def calculate_savings_ratio(savings: float, monthly_income: float) -> float:
    """Savings as a percentage of monthly income."""
    return _safe_divide(float(savings), float(monthly_income)) * 100


def calculate_expense_ratio(total_expenses: float, monthly_income: float) -> float:
    """Total expenses as a percentage of monthly income."""
    return _safe_divide(float(total_expenses), float(monthly_income)) * 100


def calculate_preliminary_score(
    savings_ratio: float,
    remaining_income: float,
    expense_ratio: float,
    debt_ratio: float,
) -> int:
    """
    Weighted 0-100 heuristic combining:
      - savings ratio (higher is better)      -> 35% weight
      - leftover income being positive         -> 25% weight
      - expense ratio (lower is better)        -> 25% weight
      - debt burden (lower is better)          -> 15% weight

    This is a rule-based PRELIMINARY score computed purely in Python.
    It is distinct from the LLM-generated "financial_health_score",
    which the AI produces using this score plus qualitative context.
    """
    # Savings component: 0 at 0% saved, 100 at >=30% saved
    savings_component = min(max(savings_ratio / 30.0, 0), 1) * 100

    # Leftover component: 100 if nothing is left unaccounted for and income
    # isn't fully consumed, 0 if remaining income is zero or negative.
    leftover_component = 0.0 if remaining_income <= 0 else min(
        max(100 - expense_ratio, 0), 100
    )

    # Expense ratio component: 100 at 0% expense ratio, 0 at >=100%
    expense_component = min(max(100 - expense_ratio, 0), 100)

    # Debt component: 100 at 0% debt ratio, 0 at >=40% debt ratio
    debt_component = min(max(100 - (debt_ratio / 40.0) * 100, 0), 100)

    score = (
        savings_component * 0.35
        + leftover_component * 0.25
        + expense_component * 0.25
        + debt_component * 0.15
    )
    return int(round(min(max(score, 0), 100)))


def score_band(score: int) -> str:
    """Human-readable band for a 0-100 score (educational only)."""
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Generally Healthy"
    if score >= 40:
        return "Needs Improvement"
    return "High Attention"
