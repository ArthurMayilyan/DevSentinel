from typing import Any

from review_run_comparison import (
    compare_review_runs,
    review_run_comparison_to_dict,
)


def mcp_compare_review_runs(
    *,
    old_run_dir: str,
    new_run_dir: str,
    comparisons_dir: str = "",
) -> dict[str, Any]:
    result = compare_review_runs(
        old_run_dir=old_run_dir,
        new_run_dir=new_run_dir,
        comparisons_dir=comparisons_dir,
    )

    return review_run_comparison_to_dict(
        result,
    )