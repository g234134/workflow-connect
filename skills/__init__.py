"""
J-line skills: metrics-aware tool wrappers (M/P/Q/O integration).

See ``skills/skills_contract.md`` for the v0.1 contract.
"""

from skills.example_skill_pg_query import run_skill_pg_query
from skills.example_skill_retrieve import run_skill_retrieve
from skills.skill_answer_for_ask import run_skill_answer_for_ask
from skills.skill_retrieve_for_ask import run_skill_retrieve_for_ask
from skills.skill_runner import SkillResult, run_metrics_aware_skill

__all__ = [
    "SkillResult",
    "run_metrics_aware_skill",
    "run_skill_retrieve",
    "run_skill_pg_query",
    "run_skill_retrieve_for_ask",
    "run_skill_answer_for_ask",
]
