import json

from list_mcp_tools import run_from_args


def test_run_from_args_lists_all_tools():
    output = run_from_args([])

    assert output.splitlines() == [
        "list_files",
        "read_file",
        "search_in_files",
        "search_knowledge",
        "add_finding",
        "write_report",
        "review_project",
        "compare_review_runs",
    ]


def test_run_from_args_lists_rag_qa_tools():
    output = run_from_args(
        [
            "--mode",
            "rag_qa",
        ]
    )

    assert output.splitlines() == [
        "search_knowledge",
    ]


def test_run_from_args_lists_code_review_tools():
    output = run_from_args(
        [
            "--mode",
            "code_review",
        ]
    )

    assert output.splitlines() == [
        "list_files",
        "read_file",
        "search_in_files",
        "search_knowledge",
        "add_finding",
        "write_report",
        "review_project",
        "compare_review_runs",
    ]


def test_run_from_args_returns_json_specs():
    output = run_from_args(
        [
            "--mode",
            "rag_qa",
            "--json",
        ]
    )

    payload = json.loads(
        output,
    )

    assert payload[0]["name"] == "search_knowledge"
    assert "input_schema" in payload[0]


def test_run_from_args_returns_mcp_json_specs():
    output = run_from_args(
        [
            "--mode",
            "rag_qa",
            "--mcp-json",
        ]
    )

    payload = json.loads(
        output,
    )

    assert payload == [
        {
            "name": "search_knowledge",
            "description": "Search the attached RAG knowledge base.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Knowledge search query.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Maximum number of chunks to return.",
                    },
                },
                "required": [
                    "query",
                ],
                "additionalProperties": False,
            },
        }
    ]