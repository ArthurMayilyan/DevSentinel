from agent import Agent
from agent_config import AgentConfig
from rag_agent_prompt import (
    build_rag_qa_prompt_builder,
)
from rag_defaults import (
    DEFAULT_RAG_AGENT_MAX_STEPS,
)
from rag_qa_llm import DeterministicRagQaLLM
from trace import TraceRecorder


def build_rag_qa_agent(
    *,
    rag_store,
    max_steps: int = DEFAULT_RAG_AGENT_MAX_STEPS,
    trace_recorder: TraceRecorder | None = None,
    llm=None,
) -> Agent:
    if trace_recorder is None:
        trace_recorder = TraceRecorder()

    if llm is None:
        llm = DeterministicRagQaLLM()

    return Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        rag_store=rag_store,
        config=AgentConfig(
            max_steps=max_steps,
            require_report_for_final_answer=False,
            require_all_python_files_processed_for_final_answer=False,
        ),
        prompt_builder=build_rag_qa_prompt_builder(),
    )