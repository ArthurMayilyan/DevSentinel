from devsentinel.core.agent import Agent
from devsentinel.llm.real_llm import RealLLM
from devsentinel.core.trace import TraceRecorder
from devsentinel.cli.cli_project_scope import build_cli_project_scope
from pathlib import Path


def main():
    llm = RealLLM()
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        project_scope=build_cli_project_scope(
            project_root=None,
            path="./sample_project",
            launch_dir=Path.cwd(),
        ),
        max_steps=20
    )

    result = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    print(result)


if __name__ == "__main__":
    main()