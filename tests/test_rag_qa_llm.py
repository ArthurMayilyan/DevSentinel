from rag_qa_llm import DeterministicRagQaLLM


def test_rag_qa_llm_extracts_evidence_from_json_observation_string():
    llm = DeterministicRagQaLLM()

    evidence = llm.extract_latest_evidence(
        [
            {
                "role": "user",
                "content": "token expiration",
            },
            {
                "role": "tool",
                "content": (
                    'Observation: '
                    '[{"source": "security.md", '
                    '"text": "Token expiration policy: tokens must be signed."}]'
                ),
            },
        ]
    )

    assert evidence == [
        {
            "source": "security.md",
            "text": "Token expiration policy: tokens must be signed.",
        }
    ]


def test_rag_qa_llm_extracts_evidence_from_tool_result_dict():
    llm = DeterministicRagQaLLM()

    evidence = llm.extract_latest_evidence(
        [
            {
                "role": "tool",
                "content": {
                    "tool_result": [
                        {
                            "source": "security.md",
                            "text": "Token expiration policy.",
                        }
                    ]
                },
            }
        ]
    )

    assert evidence == [
        {
            "source": "security.md",
            "text": "Token expiration policy.",
        }
    ]


def test_rag_qa_llm_builds_final_answer_from_evidence():
    llm = DeterministicRagQaLLM()
    llm.call_count = 1

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "token expiration",
            },
            {
                "role": "tool",
                "content": [
                    {
                        "source": "security.md",
                        "text": "Token expiration policy.",
                    }
                ],
            },
        ]
    )

    assert output == {
        "type": "final_answer",
        "answer": "Token expiration policy.\n\nSource: security.md",
    }

def test_rag_qa_llm_extracts_evidence_from_embedded_python_list_string():
    llm = DeterministicRagQaLLM()

    evidence = llm.extract_latest_evidence(
        [
            {
                "role": "user",
                "content": (
                    "Observation from search_knowledge: "
                    "[{'source': 'security.md', "
                    "'text': 'Token expiration policy: tokens must be signed.'}]"
                ),
            },
        ]
    )

    assert evidence == [
        {
            "source": "security.md",
            "text": "Token expiration policy: tokens must be signed.",
        }
    ]

def test_rag_qa_llm_accepts_content_field_as_evidence_text():
    llm = DeterministicRagQaLLM()

    evidence = llm.extract_latest_evidence(
        [
            {
                "role": "tool",
                "content": [
                    {
                        "source": "security.md",
                        "content": "Token expiration policy.",
                    }
                ],
            },
        ]
    )

    assert evidence == [
        {
            "source": "security.md",
            "content": "Token expiration policy.",
        }
    ]        

def test_rag_qa_llm_composes_short_answer_from_noisy_evidence():
    llm = DeterministicRagQaLLM()
    llm.call_count = 1

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "token expiration",
            },
            {
                "role": "tool",
                "content": [
                    {
                        "source": "security.md",
                        "text": (
                            "# Security Policy\n\n"
                            "Token expiration policy: tokens must be signed and must expire.\n"
                            "Credentials must not be hardcoded in source code.\n"
                            "Debug mode must be disabled in production."
                        ),
                    }
                ],
            },
        ]
    )

    assert output == {
        "type": "final_answer",
        "answer": (
            "Token expiration policy: tokens must be signed and must expire.\n\n"
            "Source: security.md"
        ),
    }

        