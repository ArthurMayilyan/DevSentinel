from rag_qa_llm import DeterministicRagQaLLM


RAG_QA_LLM_DETERMINISTIC = "deterministic"
RAG_QA_LLM_OPENAI = "openai"

SUPPORTED_RAG_QA_LLMS = {
    RAG_QA_LLM_DETERMINISTIC,
    RAG_QA_LLM_OPENAI,
}


def validate_rag_qa_llm_name(
    name: str,
) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("llm name must be a non-empty string.")

    if name not in SUPPORTED_RAG_QA_LLMS:
        raise ValueError(f"unsupported RAG QA LLM: {name}")


def build_rag_qa_llm(
    *,
    name: str,
    model: str,
):
    validate_rag_qa_llm_name(
        name,
    )

    if name == RAG_QA_LLM_DETERMINISTIC:
        return DeterministicRagQaLLM()

    if name == RAG_QA_LLM_OPENAI:
        from openai_rag_qa_llm import OpenAIRagQaLLM

        return OpenAIRagQaLLM(
            model=model,
        )

    raise ValueError(f"unsupported RAG QA LLM: {name}")