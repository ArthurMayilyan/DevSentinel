REVIEWER_DETERMINISTIC = "deterministic"
REVIEWER_OPENAI = "openai"

SUPPORTED_REVIEWERS = {
    REVIEWER_DETERMINISTIC,
    REVIEWER_OPENAI,
}

DEFAULT_REVIEWER = REVIEWER_DETERMINISTIC
DEFAULT_OPENAI_REVIEW_MODEL = "gpt-5.6-luna"


def validate_reviewer(
    reviewer: str,
) -> str:
    if not reviewer:
        return DEFAULT_REVIEWER

    if reviewer not in SUPPORTED_REVIEWERS:
        supported = ", ".join(
            sorted(
                SUPPORTED_REVIEWERS,
            )
        )

        raise ValueError(
            f"unsupported reviewer: {reviewer}. Supported reviewers: {supported}"
        )

    return reviewer