from agent import Agent
from real_llm import RealLLM
from trace import TraceRecorder


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