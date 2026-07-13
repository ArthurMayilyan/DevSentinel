from agent import Agent
from fake_llm import FakeLLM
from trace import TraceRecorder


def main():
    llm = FakeLLM()
    trace_recorder = TraceRecorder()

    agent = Agent(
        llm=llm,
        trace_recorder=trace_recorder,
        max_steps=12
    )

    result = agent.run(
        "Review the sample project and find possible security or maintainability issues."
    )

    print(result)


if __name__ == "__main__":
    main()