from devsentinel.core.agent import Agent
from devsentinel.llm.real_llm import RealLLM
from devsentinel.core.trace import TraceRecorder


def main():
    llm = RealLLM()
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=20
    )

    result = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    print(result)


if __name__ == "__main__":
    main()