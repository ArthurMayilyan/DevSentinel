from dataclasses import dataclass


@dataclass(frozen=True)
class RagQueryPlan:
    original_query: str
    subqueries: list[str]


def normalize_query(
    query: str,
) -> str:
    return " ".join(
        query.lower().split()
    )


def query_contains_any(
    *,
    query: str,
    terms: set[str],
) -> bool:
    normalized_query = normalize_query(
        query,
    )

    return any(
        term in normalized_query
        for term in terms
    )


def append_unique(
    *,
    values: list[str],
    value: str,
) -> None:
    if value not in values:
        values.append(
            value,
        )


def plan_rag_subqueries(
    *,
    query: str,
    max_subqueries: int = 3,
) -> RagQueryPlan:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")

    if type(max_subqueries) is not int:
        raise ValueError("max_subqueries must be an integer.")

    if max_subqueries <= 0:
        raise ValueError("max_subqueries must be greater than 0.")

    subqueries = []

    if query_contains_any(
        query=query,
        terms={
            "credential",
            "credentials",
            "secret",
            "secrets",
            "password",
            "hardcoded",
        },
    ):
        if "production" in normalize_query(
            query,
        ):
            append_unique(
                values=subqueries,
                value="credentials production",
            )
        else:
            append_unique(
                values=subqueries,
                value="credentials",
            )

    if query_contains_any(
        query=query,
        terms={
            "debug",
            "debug mode",
        },
    ):
        if "production" in normalize_query(
            query,
        ):
            append_unique(
                values=subqueries,
                value="debug mode production",
            )
        else:
            append_unique(
                values=subqueries,
                value="debug mode",
            )

    if query_contains_any(
        query=query,
        terms={
            "token",
            "tokens",
            "expiration",
            "expire",
            "signed",
        },
    ):
        append_unique(
            values=subqueries,
            value="token expiration",
        )

    if query_contains_any(
        query=query,
        terms={
            "small function",
            "small functions",
            "function",
            "functions",
        },
    ):
        append_unique(
            values=subqueries,
            value="small function",
        )

    if not subqueries:
        subqueries = [
            query,
        ]

    return RagQueryPlan(
        original_query=query,
        subqueries=subqueries[:max_subqueries],
    )