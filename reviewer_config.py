from app_settings import get_app_settings


REVIEWER_DETERMINISTIC = "deterministic"
REVIEWER_OPENAI = "openai"

SUPPORTED_REVIEWERS = {
    REVIEWER_DETERMINISTIC,
    REVIEWER_OPENAI,
}


_SETTINGS = get_app_settings()

DEFAULT_REVIEWER = _SETTINGS.review.default_reviewer

DEFAULT_OPENAI_REVIEW_MODEL = (
    _SETTINGS.openai.model
)

DEFAULT_OPENAI_REVIEW_MAX_CONTENT_CHARS = (
    _SETTINGS.openai.review_max_content_chars
)

DEFAULT_OPENAI_REVIEW_REQUEST_TIMEOUT_SECONDS = (
    _SETTINGS.openai.request_timeout_seconds
)


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
            f"unsupported reviewer: {reviewer}. "
            f"Supported reviewers: {supported}"
        )

    return reviewer