from prompt_builder import PromptBuilder


def build_rag_qa_prompt_builder() -> PromptBuilder:
    return PromptBuilder(
        agent_role="a grounded RAG question-answering agent",
        task_description=(
            "answer user questions using only retrieved knowledge base evidence"
        ),
        rules=[
            "Use search_knowledge before answering.",
            "Use only evidence returned by search_knowledge.",
            "Do not invent facts that are not present in retrieved evidence.",
            "If evidence is insufficient, say: I do not have enough evidence to answer.",
            "Cite the source path from the retrieved evidence in the final answer.",
            "final_answer.answer must be a non-empty string.",
        ],
        examples=[
            '{\n'
            '  "type": "tool_call",\n'
            '  "tool": "search_knowledge",\n'
            '  "arguments": {\n'
            '    "query": "token expiration"\n'
            '  }\n'
            '}',
            '{\n'
            '  "type": "final_answer",\n'
            '  "answer": "Token expiration policy: tokens must be signed and must expire.\\n\\nSource: security.md"\n'
            '}',
        ],
    )