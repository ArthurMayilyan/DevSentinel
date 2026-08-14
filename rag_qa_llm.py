import ast
import json
from typing import Any

from rag_answer_composer import compose_rag_answer
from rag_evidence_extractor import (
    add_missing_subquery_context,
    extract_all_evidence,
    extract_all_evidence_with_provenance,
    extract_evidence_from_value,
    extract_latest_evidence,
    get_evidence_source,
    get_evidence_text,
)
from rag_query_planner import plan_rag_subqueries


class DeterministicRagQaLLM:
    def __init__(self):
        self.call_count = 0
        self.subqueries = []
        self.original_query = ""

    def complete(
        self,
        messages,
        state=None,
    ):
        self.call_count += 1

        if not self.original_query:
            self.original_query = self.extract_user_query(
                messages,
            )

        user_query = self.original_query

        if not self.subqueries:
            self.subqueries = plan_rag_subqueries(
                query=user_query,
            ).subqueries

        if self.call_count <= len(
            self.subqueries,
        ):
            return {
                "type": "tool_call",
                "tool": "search_knowledge",
                "arguments": {
                    "query": self.subqueries[self.call_count - 1],
                },
            }

        evidence = self.extract_all_evidence_with_provenance(
            messages,
        )
        evidence = add_missing_subquery_context(
            evidence=evidence,
            subqueries=self.subqueries,
        )        

        if not evidence:
            return {
                "type": "final_answer",
                "answer": "I do not have enough evidence to answer.",
            }

        composed_answer = compose_rag_answer(
            query=user_query,
            evidence=evidence,
            max_sentences=max(
                1,
                min(
                    len(
                        self.subqueries,
                    ),
                    3,
                ),
            ),
        )

        return {
            "type": "final_answer",
            "answer": composed_answer.answer,
        }

    def extract_all_evidence_with_provenance(
        self,
        messages,
    ) -> list[dict[str, Any]]:
        return extract_all_evidence_with_provenance(
            messages,
        )

    def extract_user_query(
        self,
        messages,
    ) -> str:
        for message in messages:
            if not isinstance(message, dict):
                continue

            if message.get("role") != "user":
                continue

            content = message.get(
                "content",
                "",
            )

            if not isinstance(content, str):
                continue

            stripped_content = content.strip()

            if not stripped_content:
                continue

            if stripped_content.startswith(
                "Observation from tool"
            ):
                continue

            if stripped_content.startswith(
                "Observation:"
            ):
                continue

            if "Choose the next valid JSON action" in stripped_content:
                continue

            return stripped_content

        return ""




    def parse_possible_structured_values(
        self,
        value: str,
    ) -> list[Any]:
        text = value.strip()

        if not text:
            return []

        parsed_values = []

        direct_parsed = self.try_parse_json_or_python_literal(
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

                parsed = self.try_parse_json_or_python_literal(
                    candidate,
                )

                if parsed is not None:
                    parsed_values.append(
                        parsed,
                    )

        embedded_candidates = self.extract_embedded_list_or_dict_strings(
            text,
        )

        for candidate in embedded_candidates:
            parsed = self.try_parse_json_or_python_literal(
                candidate,
            )

            if parsed is not None:
                parsed_values.append(
                    parsed,
                )

        return parsed_values

    def extract_embedded_list_or_dict_strings(
        self,
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

    def try_parse_json_or_python_literal(
        self,
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

    def is_evidence_list(
        self,
        value: list,
    ) -> bool:
        return bool(value) and all(
            self.is_evidence_item(
                item,
            )
            for item in value
        )

    def is_evidence_item(
        self,
        value,
    ) -> bool:
        if not isinstance(value, dict):
            return False

        source = self.get_evidence_source(
            value,
        )

        text = self.get_evidence_text(
            value,
        )

        return bool(source) and bool(text)

    def extract_latest_evidence(
        self,
        messages,
    ) -> list[dict[str, Any]]:
        return extract_latest_evidence(
            messages,
        )


    def extract_all_evidence(
        self,
        messages,
    ) -> list[dict[str, Any]]:
        return extract_all_evidence(
            messages,
        )


    def extract_evidence_from_value(
        self,
        value,
    ) -> list[dict[str, Any]]:
        return extract_evidence_from_value(
            value,
        )


    def get_evidence_source(
        self,
        value: dict[str, Any],
    ) -> str:
        return get_evidence_source(
            value,
        )


    def get_evidence_text(
        self,
        value: dict[str, Any],
    ) -> str:
        return get_evidence_text(
            value,
        )