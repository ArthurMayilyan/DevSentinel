from agent import Agent
from agent_config import AgentConfig
from rag_agent_prompt import build_rag_qa_prompt_builder
from rag_qa_llm import DeterministicRagQaLLM
from trace import TraceRecorder


def build_rag_qa_agent(
    *,
    rag_store,
    max_steps: int = 4,
) -> Agent:
    return Agent(
        llm=DeterministicRagQaLLM(),
        trace_recorder=TraceRecorder(),
        rag_store=rag_store,
        config=AgentConfig(
            max_steps=max_steps,
            require_report_for_final_answer=False,
            require_all_python_files_processed_for_final_answer=False,
        ),
        prompt_builder=build_rag_qa_prompt_builder(),
    )