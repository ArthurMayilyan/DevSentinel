"""Exercise the real OpenAI review path before a release."""

import argparse
import os

from devsentinel.llm.openai_client_factory import load_dotenv_if_available
from devsentinel.llm.openai_review_reviewer import OpenAIReviewReviewer


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run a live OpenAI review smoke check.")
    parser.add_argument(
        "--model",
        required=True,
        help="A model available to this API account.",
    )
    args = parser.parse_args(argv)

    load_dotenv_if_available()
    if not os.environ.get("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is required for the live smoke check")

    reviewer = OpenAIReviewReviewer(model=args.model)
    findings = reviewer.review_file(
        file_path="smoke_sample.py",
        content='SECRET_KEY = "hardcoded-smoke-test-secret"\n',
        profile="security",
        policy_context="Hardcoded secrets must be reported.",
    )
    if not any(
        item.get("finding_type") == "security.hardcoded_secret"
        for item in findings
    ):
        raise RuntimeError(
            "Live reviewer did not return the expected hardcoded-secret finding"
        )
    print("Live OpenAI review passed")


if __name__ == "__main__":
    main()
