SUPPORTED_TASK_PRESETS = {
    "code-review",
}

DEFAULT_CODE_REVIEW_MAX_FINDINGS = 3


def build_code_review_task(
    *,
    path: str,
    max_findings: int = DEFAULT_CODE_REVIEW_MAX_FINDINGS,
) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string.")

    if type(max_findings) is not int:
        raise ValueError("max_findings must be an integer.")

    if max_findings <= 0:
        raise ValueError("max_findings must be greater than 0.")

    normalized_path = path.strip()

    return "\n".join([
        f"Review {normalized_path} only.",
        f"Start with list_files path {normalized_path}.",
        "Read all Python files.",
        f"Add no more than {max_findings} most important findings.",
        "Then call write_report.",
        "Then return final_answer.",
        "Return exactly one JSON object per response.",
    ])


def build_task_from_preset(
    *,
    preset: str,
    path: str,
    max_findings: int = DEFAULT_CODE_REVIEW_MAX_FINDINGS,
) -> str:
    if preset == "code-review":
        return build_code_review_task(
            path=path,
            max_findings=max_findings,
        )

    raise ValueError(f"Unsupported task preset: {preset}")

