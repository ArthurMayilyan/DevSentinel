from tools import list_files, read_file, search_in_files, write_report
from tool_specs import IssueCategory, IssueSeverity
from agent_state import AgentState
from runtime_tool_registry import ToolRegistry
from default_tool_registry import build_default_tool_registry
from prompt_builder import PromptBuilder

ALLOWED_SEVERITIES = {item.value for item in IssueSeverity}
ALLOWED_CATEGORIES = {item.value for item in IssueCategory}

def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


class Agent:

    def __init__(
        self,
        llm,
        trace_recorder,
        max_steps: int = 8,
        tool_registry: ToolRegistry | None = None,
        prompt_builder: PromptBuilder | None = None,
    ):
        self.llm = llm
        self.trace_recorder = trace_recorder
        self.max_steps = max_steps
        self.prompt_builder = prompt_builder or PromptBuilder()

        self._tools = {
            "list_files": list_files,
            "read_file": read_file,
            "search_in_files": search_in_files,
            "write_report": write_report,
            "add_finding": self.add_finding,
        }

        self.tool_registry = tool_registry or build_default_tool_registry(
            tool_functions=self._tools,
        )
    
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

            if not isinstance(llm_output, dict):
                reason = (
                    f"Invalid LLM output. Expected JSON object/dict, "
                    f"got {type(llm_output).__name__}."
                )

                self.reject_llm_output(
                    trace_step=trace_step,
                    state=state,
                    messages=messages,
                    reason=reason,
                    llm_output=llm_output,
                )

                continue

            if llm_output.get("type") == "final_answer":
                answer = llm_output.get("answer")
                allowed, reason = self.validate_final_answer_allowed(state, answer)

                if not allowed:
                    self.reject_final_answer(
                        trace_step=trace_step,
                        state=state,
                        messages=messages,
                        reason=reason,
                    )

                    continue

                trace_step["final_answer"] = answer
                trace_step["state_after"] = state.to_dict()

                self.trace_recorder.record(trace_step)
                return answer

            if llm_output.get("type") != "tool_call":
                reason = "Invalid LLM output type. Use tool_call or final_answer."

                self.reject_llm_output(
                    trace_step=trace_step,
                    state=state,
                    messages=messages,
                    reason=reason,
                    llm_output=llm_output,
                )

                continue

            tool_name = llm_output.get("tool")
            arguments = llm_output.get("arguments", {})

            if "tool" not in llm_output or tool_name is None or tool_name == "":
                reason = "tool_call rejected: missing tool name."

                self.reject_tool_call(
                    trace_step=trace_step,
                    state=state,
                    messages=messages,
                    reason=reason,
                )

                continue

            if not isinstance(tool_name, str):
                reason = (
                    f"tool_call rejected: tool name must be a string. "
                    f"Got {type(tool_name).__name__}."
                )

                self.reject_tool_call(
                    trace_step=trace_step,
                    state=state,
                    messages=messages,
                    reason=reason,
                )

                continue

            if not self.tool_registry.has(tool_name):
                reason = f"Unknown tool: {tool_name}. Available tools: {self.tool_registry.names()}"

                self.reject_tool_call(
                    trace_step=trace_step,
                    state=state,
                    messages=messages,
                    reason=reason,
                )

                continue

            try:
                # Arguments originally produced by the LLM.
                # Keep them separate from runtime execution arguments.
                llm_arguments = llm_output.get("arguments", {}) or {}

                if not isinstance(llm_arguments, dict):
                    reason = (
                        f"Invalid arguments for tool `{tool_name}`. "
                        f"Expected dict, got {type(llm_arguments).__name__}."
                    )

                    self.reject_tool_call(
                        trace_step=trace_step,
                        state=state,
                        messages=messages,
                        reason=reason,
                    )

                    continue

                # Defensive copy, so we do not mutate llm_output inside the trace.
                llm_arguments = dict(llm_arguments)

                allowed, reason = self.tool_registry.validate_arguments(
                    tool_name=tool_name,
                    arguments=llm_arguments,
                )

                if not allowed:
                    self.reject_tool_call(
                        trace_step=trace_step,
                        state=state,
                        messages=messages,
                        reason=reason,
                    )

                    continue

                # ------------------------------------------------------------------
                # Runtime guardrail: add_finding is allowed only after file inspection.
                # ------------------------------------------------------------------
                if tool_name == "add_finding":
                    allowed, reason = self.validate_add_finding_allowed(
                        state=state,
                        llm_arguments=llm_arguments,
                    )

                    if not allowed:
                        self.reject_tool_call(
                            trace_step=trace_step,
                            state=state,
                            messages=messages,
                            reason=reason,
                        )

                        continue

                # ------------------------------------------------------------------
                # Runtime guardrail: write_report is allowed only after inspection
                # and after at least one finding has been added.
                # ------------------------------------------------------------------
                if tool_name == "write_report":
                    discovered_files = {
                        normalize_path(path)
                        for path in state.discovered_files
                        if normalize_path(path).endswith(".py")
                    }

                    inspected_files = {
                        normalize_path(path)
                        for path in state.inspected_files
                    }

                    skipped_files = {
                        normalize_path(path)
                        for path in state.skipped_files.keys()
                    }

                    failed_files = {
                        normalize_path(path)
                        for path in state.failed_files.keys()
                    }

                    completed_files = inspected_files | skipped_files | failed_files
                    missing_files = sorted(discovered_files - completed_files)

                    if not discovered_files:
                        reason = (
                            "write_report rejected: no files have been discovered. "
                            "Call list_files before writing the report."
                        )

                        self.reject_tool_call(
                            trace_step=trace_step,
                            state=state,
                            messages=messages,
                            reason=reason,
                        )

                        continue

                    if missing_files:
                        reason = (
                            "write_report rejected: not all discovered Python files have been "
                            f"inspected, skipped, or failed. Missing files: {missing_files}"
                        )

                        self.reject_tool_call(
                            trace_step=trace_step,
                            state=state,
                            messages=messages,
                            reason=reason,
                        )

                        continue

                    if not state.findings:
                        reason = (
                            "write_report rejected: no findings have been added. "
                            "Call add_finding before writing the report."
                        )

                        self.reject_tool_call(
                            trace_step=trace_step,
                            state=state,
                            messages=messages,
                            reason=reason,
                        )

                        continue

                self.execute_tool_call(
                    state=state,
                    messages=messages,
                    trace_step=trace_step,
                    tool_name=tool_name,
                    llm_arguments=llm_arguments,
                )

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
        return self.tool_registry.format_tools_for_prompt()

    def validate_final_answer_allowed(self, state: AgentState, answer: object) -> tuple[bool, str]:
        if not isinstance(answer, str):
            return False, "final_answer rejected: answer must be a string."

        if not answer.strip():
            return False, "final_answer rejected: answer must be a non-empty string."

        if not state.report_written:
            return False, "final_answer rejected: report has not been written yet."

        if not state.report_path:
            return False, "final_answer rejected: report_path is missing."
    
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
        return self.prompt_builder.build_system_prompt(
            tools_description=self.build_tools_description(),
        )

    def reject_tool_call(
        self,
        *,
        trace_step: dict,
        state: AgentState,
        messages: list[dict],
        reason: str,
    ) -> None:
        trace_step["tool_result"] = None
        trace_step["error"] = reason
        state.errors.append(reason)
        trace_step["state_after"] = state.to_dict()

        self.trace_recorder.record(trace_step)

        messages.append({
            "role": "user",
            "content": (
                f"Tool call rejected:\n{reason}\n\n"
                "Choose the next valid JSON action."
            )
        })


    def reject_llm_output(
        self,
        *,
        trace_step: dict,
        state: AgentState,
        messages: list[dict],
        reason: str,
        llm_output: object,
    ) -> None:
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
                "Return only valid JSON object with type tool_call or final_answer."
            )
        })

    def reject_final_answer(
        self,
        *,
        trace_step: dict,
        state: AgentState,
        messages: list[dict],
        reason: str,
    ) -> None:
        state.rejected_final_answer_count += 1
        state.errors.append(reason)

        trace_step["guardrail_result"] = {
            "name": "completion_guardrail",
            "allowed": False,
            "reason": reason,
        }
        trace_step["tool_result"] = None
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

    def execute_tool_call(
        self,
        *,
        state: AgentState,
        messages: list[dict],
        trace_step: dict,
        tool_name: str,
        llm_arguments: dict,
    ) -> None:
        execution_arguments = dict(llm_arguments)
        observation_arguments = dict(llm_arguments)

        if tool_name == "write_report":
            execution_arguments = {
                "state": state
            }
            observation_arguments = {}

        tool_function = self.tool_registry.function(tool_name)
        tool_result = tool_function(**execution_arguments)

        if tool_name == "write_report":
            state.report_written = True
            state.report_path = tool_result

        trace_step["tool_result"] = tool_result

        self.update_state_after_tool_call(
            state=state,
            tool_name=tool_name,
            arguments=observation_arguments,
            tool_result=tool_result,
        )

        messages.append({
            "role": "user",
            "content": (
                f"Observation from tool `{tool_name}` with arguments {observation_arguments}:\n"
                f"{tool_result}\n\n"
                "Choose the next valid JSON action."
            )
        })        

    def validate_add_finding_allowed(
        self,
        *,
        state: AgentState,
        llm_arguments: dict,
    ) -> tuple[bool, str]:
        finding_file = normalize_path(llm_arguments.get("file", ""))

        inspected_files = {
            normalize_path(path)
            for path in state.inspected_files
        }

        if not finding_file:
            return False, "add_finding rejected: missing required file argument."

        if finding_file not in inspected_files:
            return (
                False,
                (
                    f"add_finding rejected: file `{finding_file}` has not been inspected. "
                    "Call read_file for this file before adding findings."
                ),
            )

        return True, ""        
    
