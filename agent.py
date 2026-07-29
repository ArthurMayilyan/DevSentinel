from tools import list_files, read_file, search_in_files, write_report
from tool_specs import TOOL_SPECS, IssueCategory, IssueSeverity
from agent_state import AgentState




class Agent:

    def __init__(self, llm, trace_recorder, max_steps: int = 8):
        self.tool_specs = TOOL_SPECS
        self.llm = llm
        self.trace_recorder = trace_recorder
        self.max_steps = max_steps

        self.tools = {
            "list_files": list_files,
            "read_file": read_file,
            "search_in_files": search_in_files,
            "write_report": write_report,
            "add_finding": self.add_finding,
        }
    
    def run(self, user_task: str) -> str:
        state = AgentState()
        self.state = state

        messages = [
            {
                "role": "system",
                "content": self.build_system_prompt()
            },
            {
                "role": "user",
                "content": user_task
            }
        ]

        for step in range(1, self.max_steps + 1):
            trace_step = {
                "step": step,
                "llm_output": None,
                "tool_result": None,
                "error": None,
                "state_before": state.to_dict(),
            }

            llm_output = self.llm.complete(messages, state)
            trace_step["llm_output"] = llm_output

            if llm_output.get("type") == "final_answer":
                allowed, reason = self.validate_final_answer_allowed(state)

                if not allowed:
                    state.rejected_final_answer_count += 1
                    state.errors.append(reason)

                    trace_step["guardrail_result"] = {
                        "name": "completion_guardrail",
                        "allowed": False,
                        "reason": reason,
                    }
                    trace_step["error"] = None
                    trace_step["state_after"] = state.to_dict()

                    self.trace_recorder.record(trace_step)

                    messages.append({
                        "role": "user",
                        "content": (
                            f"Final answer rejected by completion guardrail:\n"
                            f"{reason}\n\n"
                            "Choose the next valid JSON action."
                        )
                    })

                    continue           
                trace_step["final_answer"] = llm_output.get("answer")
                trace_step["state_after"] = state.to_dict()

                self.trace_recorder.record(trace_step)
                return llm_output.get("answer", "")

            if llm_output.get("type") != "tool_call":
                reason = "Invalid LLM output type. Use tool_call or final_answer."

                trace_step["error"] = reason
                state.errors.append(reason)
                trace_step["state_after"] = state.to_dict()

                self.trace_recorder.record(trace_step)

                messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous output was invalid:\n"
                        f"{llm_output}\n\n"
                        f"{reason}\n"
                        "Return only valid JSON."
                    )
                })

                continue

            tool_name = llm_output.get("tool")
            arguments = llm_output.get("arguments", {})

            if tool_name not in self.tools:
                reason = f"Unknown tool: {tool_name}. Available tools: {list(self.tools.keys())}"

                trace_step["error"] = reason
                state.errors.append(reason)
                trace_step["state_after"] = state.to_dict()

                self.trace_recorder.record(trace_step)

                messages.append({
                    "role": "user",
                    "content": (
                        f"{reason}\n\n"
                        "Choose the next valid JSON action using only available tools."
                    )
                })

                continue

            try:
                if tool_name == "write_report":
                    arguments = {
                        **arguments,
                        "state": state,
                    }

                tool_result = self.tools[tool_name](**arguments)

                if tool_name == "write_report":
                    state.report_written = True
                    state.report_path = tool_result

                trace_step["tool_result"] = tool_result

                self.update_state_after_tool_call(
                    state=state,
                    tool_name=tool_name,
                    arguments=arguments,
                    tool_result=tool_result
                )

                messages.append({
                    "role": "user",
                    "content": (
                        f"Observation from tool `{tool_name}` with arguments {arguments}:\n"
                        f"{tool_result}\n\n"
                        "Choose the next valid JSON action."
                    )
                })

            except Exception as error:
                error_message = repr(error)

                trace_step["error"] = error_message
                state.errors.append(error_message)

                messages.append({
                    "role": "user",
                    "content": (
                        f"Tool `{tool_name}` failed with error:\n"
                        f"{error_message}\n\n"
                        "Choose the next valid JSON action."
                    )
                })
            trace_step["state_after"] = state.to_dict()
            self.trace_recorder.record(trace_step)

        return "Agent stopped because max_steps limit was reached."
    

    def build_tools_description(self) -> str:
        descriptions = []

        for tool in self.tool_specs.values():
            descriptions.append(
                f"""
Tool: {tool.name}
Description: {tool.description}
Parameters: {tool.parameters}
Returns: {tool.returns}
When to use: {tool.when_to_use}
When not to use: {tool.when_not_to_use}
"""
            )

        return "\n".join(descriptions)

    def validate_final_answer_allowed(self, state: AgentState) -> tuple[bool, str]:
        python_files = [
            file for file in state.discovered_files
            if file.endswith(".py")
        ]

        unprocessed_files = [
            file for file in python_files
            if file not in state.inspected_files
            and file not in state.skipped_files
        ]

        if unprocessed_files:
            state.rejected_final_answer_count += 1
            return (
                False,
                f"Cannot finish yet. Unprocessed files: {unprocessed_files}"
            )

        if not state.report_written:
            state.rejected_final_answer_count += 1
            return (
                False,
                "Cannot finish yet. Report has not been written."
            )

        return True, ""
    

    def update_state_after_tool_call(
        self,
        state,
        tool_name: str,
        arguments: dict,
        tool_result
    ) -> None:
        state.tools_used.append(tool_name)

        if tool_name == "list_files":
            state.discovered_files = tool_result

        elif tool_name == "read_file":
            path = arguments.get("path")
            if path and path not in state.inspected_files:
                state.inspected_files.append(path)

        elif tool_name == "write_report":
            state.report_written = True


    def validate_findings_have_evidence(state: AgentState) -> tuple[bool, str]:
        for finding in state.findings:
            if not finding.get("file"):
                return False, "Finding is missing file reference."

            if not finding.get("evidence"):
                return False, "Finding is missing evidence."

            if not finding.get("severity"):
                return False, "Finding is missing severity."

        return True, ""
    
    def normalize_enum_value(self, value: str, enum_cls):
        try:
            return enum_cls(value).value
        except ValueError:
            upper_value = value.upper()
            try:
                return enum_cls(upper_value).value
            except ValueError:
                allowed = [item.value for item in enum_cls]
                raise ValueError(f"Invalid value: {value}. Allowed values: {allowed}")
    
    def add_finding(self, file, severity, category, issue, evidence, recommendation):
        severity = self.normalize_enum_value(severity, IssueSeverity)
        category = self.normalize_enum_value(category, IssueCategory)

        finding = {
            "file": file,
            "severity": severity,
            "category": category,
            "issue": issue,
            "evidence": evidence,
            "recommendation": recommendation,
        }

        self.state.findings.append(finding)
        return "Finding added."


    def build_system_prompt(self) -> str:
            return f"""
        You are a code review agent.

        You must respond ONLY with valid JSON.

        You can choose one of two actions:

        1. Tool call:
        {{
        "type": "tool_call",
        "tool": "<tool_name>",
        "arguments": {{ }}
        }}

        2. Final answer:
        {{
        "type": "final_answer",
        "answer": "<human-readable final answer>"
        }}

        Available tools:
        {self.build_tools_description()}

        Allowed severity values:
        LOW, MEDIUM, HIGH

        Allowed category values:
        SECURITY, MAINTAINABILITY, RELIABILITY, PERFORMANCE

        Rules:
        - Do not call tools that are not listed.
        - Call list_files first to discover files.
        - Use read_file before adding findings for a file.
        - Use add_finding for each issue before writing the report.
        - Do not call write_report until findings are collected.
        - Do not produce final_answer until all relevant discovered Python files are inspected.
        - Every finding must include file, severity, category, issue, evidence, and recommendation.
        - Use only allowed enum values for severity and category.
        - Do not invent file paths.
        - Do not include markdown or explanations outside JSON.
        """.strip()