import ast
import json
from typing import Any
import re

from rag_evidence import (
    RagEvidenceItem,
    deduplicate_evidence_items,
    evidence_item_from_dict,
    evidence_items_to_dicts,
)


def get_evidence_source(
    value: dict[str, Any],
) -> str:
    for key in [
        "source",
        "file",
        "path",
    ]:
        item = value.get(
            key,
        )

        if isinstance(item, str) and item.strip():
            return item

    return ""


def get_evidence_text(
    value: dict[str, Any],
) -> str:
    for key in [
        "text",
        "content",
        "chunk_text",
        "snippet",
    ]:
        item = value.get(
            key,
        )

        if isinstance(item, str) and item.strip():
            return item

    return ""


def is_evidence_item(
    value,
) -> bool:
    return (
        isinstance(value, dict)
        and bool(
            get_evidence_source(
                value,
            )
        )
        and bool(
            get_evidence_text(
                value,
            )
        )
    )


def is_evidence_list(
    value: list,
) -> bool:
    return bool(value) and all(
        is_evidence_item(
            item,
        )
        for item in value
    )


def try_parse_json_or_python_literal(
    value: str,
):
    try:
        return json.loads(
            value,
        )
    except json.JSONDecodeError:
        pass

    try:
        return ast.literal_eval(
            value,
        )
    except (ValueError, SyntaxError):
        return None


def extract_embedded_list_or_dict_strings(
    text: str,
) -> list[str]:
    candidates = []

    list_start = text.find("[")
    list_end = text.rfind("]")

    if list_start != -1 and list_end != -1 and list_end > list_start:
        candidates.append(
            text[list_start:list_end + 1],
        )

    dict_start = text.find("{")
    dict_end = text.rfind("}")

    if dict_start != -1 and dict_end != -1 and dict_end > dict_start:
        candidates.append(
            text[dict_start:dict_end + 1],
        )

    return candidates


def parse_possible_structured_values(
    value: str,
) -> list[Any]:
    text = value.strip()

    if not text:
        return []

    parsed_values = []

    direct_parsed = try_parse_json_or_python_literal(
        text,
    )

    if direct_parsed is not None:
        parsed_values.append(
            direct_parsed,
        )

    for prefix in [
        "Observation:",
        "observation:",
        "Tool result:",
        "tool result:",
        "tool_result:",
        "Result:",
        "result:",
    ]:
        if text.startswith(prefix):
            candidate = text[len(prefix):].strip()

            parsed = try_parse_json_or_python_literal(
                candidate,
            )

            if parsed is not None:
                parsed_values.append(
                    parsed,
                )

    for candidate in extract_embedded_list_or_dict_strings(
        text,
    ):
        parsed = try_parse_json_or_python_literal(
            candidate,
        )

        if parsed is not None:
            parsed_values.append(
                parsed,
            )

    return parsed_values


def extract_evidence_from_value(
    value,
) -> list[dict[str, Any]]:
    if isinstance(value, list):
        if is_evidence_list(
            value,
        ):
            return value

        evidence = []

        for item in value:
            evidence.extend(
                extract_evidence_from_value(
                    item,
                )
            )

        return evidence

    if isinstance(value, dict):
        if is_evidence_item(
            value,
        ):
            return [
                value,
            ]

        evidence = []

        for key in [
            "content",
            "result",
            "tool_result",
            "observation",
            "output",
            "data",
            "message",
        ]:
            if key not in value:
                continue

            evidence.extend(
                extract_evidence_from_value(
                    value[key],
                )
            )

        return evidence

    if isinstance(value, str):
        evidence = []

        for parsed_value in parse_possible_structured_values(
            value,
        ):
            evidence.extend(
                extract_evidence_from_value(
                    parsed_value,
                )
            )

        return evidence

    return []


def deduplicate_evidence(
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deduplicated = []
    seen = set()

    for item in evidence:
        key = (
            get_evidence_source(
                item,
            ),
            item.get(
                "chunk_index",
            ),
            get_evidence_text(
                item,
            ),
        )

        if key in seen:
            continue

        deduplicated.append(
            item,
        )
        seen.add(
            key,
        )

    return deduplicated


def extract_latest_evidence(
    values,
) -> list[dict[str, Any]]:
    for value in reversed(
        values,
    ):
        evidence = extract_evidence_from_value(
            value,
        )

        if evidence:
            return deduplicate_evidence(
                evidence,
            )

    return []


def extract_all_evidence(
    values,
) -> list[dict[str, Any]]:
    evidence = []

    for value in values:
        evidence.extend(
            extract_evidence_from_value(
                value,
            )
        )

    return deduplicate_evidence(
        evidence,
    )

def extract_query_from_observation_text(
    text: str,
) -> str:
    match = re.search(
        r"arguments\s+(\{.*?\})",
        text,
        flags=re.DOTALL,
    )

    if match is None:
        return ""

    parsed = try_parse_json_or_python_literal(
        match.group(
            1,
        )
    )

    if not isinstance(parsed, dict):
        return ""

    query = parsed.get(
        "query",
        "",
    )

    if not isinstance(query, str):
        return ""

    return query


def annotate_evidence_with_subquery(
    *,
    evidence: list[dict[str, Any]],
    subquery: str,
    subquery_index: int,
    strategy: str = "",
) -> list[dict[str, Any]]:
    annotated = []

    for item in evidence:
        if not isinstance(item, dict):
            continue

        copied_item = dict(
            item,
        )
        copied_item["subquery"] = subquery
        copied_item["subquery_index"] = subquery_index
        copied_item["strategy"] = strategy

        annotated.append(
            copied_item,
        )

    return annotated


def extract_all_evidence_items(
    values,
    *,
    strategy: str = "",
) -> list[RagEvidenceItem]:
    items = []
    subquery_indexes = {}

    for value in values:
        subquery = ""

        if isinstance(value, dict):
            arguments = value.get(
                "arguments",
            )

            if isinstance(arguments, dict):
                maybe_query = arguments.get(
                    "query",
                )

                if isinstance(maybe_query, str):
                    subquery = maybe_query

            content = value.get(
                "content",
            )

            if isinstance(content, str) and not subquery:
                subquery = extract_query_from_observation_text(
                    content,
                )

        if isinstance(value, str):
            subquery = extract_query_from_observation_text(
                value,
            )

        evidence = extract_evidence_from_value(
            value,
        )

        if not evidence:
            continue

        if subquery not in subquery_indexes:
            subquery_indexes[subquery] = len(
                subquery_indexes,
            )

        subquery_index = subquery_indexes[
            subquery
        ]

        for item in annotate_evidence_with_subquery(
            evidence=evidence,
            subquery=subquery,
            subquery_index=subquery_index,
            strategy=strategy,
        ):
            evidence_item = evidence_item_from_dict(
                value=item,
                subquery=subquery,
                subquery_index=subquery_index,
                strategy=strategy,
            )

            if evidence_item.source and evidence_item.text:
                items.append(
                    evidence_item,
                )

    return deduplicate_evidence_items(
        items,
        keep_subquery_context=True,
    )


def extract_all_evidence_with_provenance(
    values,
    *,
    strategy: str = "",
) -> list[dict[str, Any]]:
    return evidence_items_to_dicts(
        extract_all_evidence_items(
            values,
            strategy=strategy,
        )
    )

def add_missing_subquery_context(
    *,
    evidence: list[dict[str, Any]],
    subqueries: list[str],
    strategy: str = "",
) -> list[dict[str, Any]]:
    if not subqueries:
        return evidence

    updated = []

    for index, item in enumerate(
        evidence,
    ):
        copied_item = dict(
            item,
        )

        current_subquery = copied_item.get(
            "subquery",
            "",
        )

        current_subquery_index = copied_item.get(
            "subquery_index",
            -1,
        )

        missing_subquery = not isinstance(
            current_subquery,
            str,
        ) or not current_subquery.strip()

        missing_subquery_index = (
            not isinstance(
                current_subquery_index,
                int,
            )
            or current_subquery_index < 0
        )

        if missing_subquery or missing_subquery_index:
            fallback_index = min(
                index,
                len(
                    subqueries,
                )
                - 1,
            )

            copied_item["subquery_index"] = fallback_index
            copied_item["subquery"] = subqueries[
                fallback_index
            ]

        if strategy and not copied_item.get(
            "strategy",
        ):
            copied_item["strategy"] = strategy

        updated.append(
            copied_item,
        )

    return updated