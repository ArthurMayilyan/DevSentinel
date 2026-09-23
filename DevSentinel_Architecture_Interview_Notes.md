# AgentLoop Architecture & Interview Notes

## Purpose

This document is a compact technical reference for explaining AgentLoop in interviews, architecture discussions, and future development.

AgentLoop is an **engineering-grade / production-oriented prototype** for AI-assisted engineering review. It combines deterministic controls with LLM-based contextual reasoning, RAG-backed security knowledge, Git-aware scope selection, MCP integration, persistent review artifacts, and a lightweight Web UI.

The project was intentionally built from the agent loop upward rather than starting with a high-level agent framework.

---

# 1. One-Sentence Description

> **AgentLoop is an AI-assisted engineering review platform that combines deterministic analysis, LLM-based contextual review, RAG-backed policies, Git-aware code selection, MCP/VS Code integration, evaluation, and persistent review artifacts.**

---

# 2. Architecture Overview

```text
                               +----------------------+
                               |    agentloop.toml    |
                               | models / limits /    |
                               | RAG / review presets |
                               +----------+-----------+
                                          |
                                          v
+----------------+              +----------------------+              +----------------+
| VS Code / MCP  |------------->|                      |<-------------| Local Web UI   |
+----------------+              |   AgentLoop Runtime  |              +----------------+
                                |                      |
+----------------+------------->|                      |<-------------+----------------+
| CLI / Python   |              +----------+-----------+              | Tests / Evals  |
+----------------+                         |                          +----------------+
                                           |
                    +----------------------+----------------------+
                    |                      |                      |
                    v                      v                      v
             Workspace Review       Git Diff Review        Staged Review
                    |                      |                      |
                    +----------------------+----------------------+
                                           |
                                           v
                                  Scope / File Selection
                                           |
                              +------------+-------------+
                              |                          |
                              v                          v
                    Deterministic Reviewer        OpenAI Reviewer
                              |                          |
                              |                   +------+------+
                              |                   | Security KB |
                              |                   | RAG Context |
                              |                   +------+------+
                              |                          |
                              +------------+-------------+
                                           |
                                           v
                                        Findings
                                           |
                                           v
                                  Stable Finding Types
                                           |
                                           v
                          Markdown / HTML / JSON Artifacts
                                           |
                              +------------+-------------+
                              |                          |
                              v                          v
                         Run History              Run Comparison
```

---

# 3. Main Architectural Layers

## 3.1 Agent Core

The original core is a custom tool-using agent loop.

Main responsibilities:

- hold and mutate agent state;
- call the LLM;
- validate model output;
- validate tool calls;
- execute tools;
- append observations;
- enforce guardrails;
- stop on completion or configured limits;
- record trace/state transitions.

The important design idea is:

```text
LLM proposes actions.
Application code decides whether they are allowed.
```

The LLM is not treated as the security or control boundary.

### Core agent concepts implemented

- structured LLM output;
- tool registry and tool contracts;
- state_before / state_after tracing;
- final-answer guardrails;
- rejected tool-call tracking;
- invalid-output tracking;
- max-step limits;
- explicit stop reasons.

---

## 3.2 Tool Layer

Low-level tools include:

```text
list_files
read_file
search_in_files
search_knowledge
add_finding
write_report
```

Product-level MCP tools include:

```text
review_project
review_workspace
review_git_diff
compare_review_runs
```

The design evolved from low-level agent tools to higher-level product workflows.

This was important because a user or external MCP client should not have to reproduce the internal sequence:

```text
list -> read -> retrieve policy -> review -> add findings -> write report
```

A high-level tool can encapsulate that workflow consistently.

---

## 3.3 RAG Layer

AgentLoop contains a custom RAG pipeline rather than a single opaque retrieval call.

Conceptually:

```text
Documents
    |
    v
Loader
    |
    v
Chunking
    |
    v
RAG Store / Persistent Index
    |
    v
Retriever Strategy
    |
    v
Evidence + Provenance
    |
    v
Composer / LLM
    |
    v
Grounded Answer
```

Implemented concepts include:

- document loading;
- chunking with overlap;
- multiple retrieval strategies;
- strategy selection;
- persistent index;
- evidence provenance;
- query-aware composition;
- multi-step/agentic retrieval;
- grounding validation;
- retrieval and answer evaluation.

### Why multiple retrieval strategies matter

One useful learning result was that frequency-based retrieval can rank repeated noise too highly.

Example:

```text
Document A:
token token token token

Document B:
token expiration
```

For query:

```text
token expiration
```

a naive term-frequency method can overvalue Document A.

A binary-overlap approach can instead prefer coverage of distinct query terms.

This is a good interview example because it demonstrates that RAG quality depends heavily on retrieval semantics, not just the LLM.

---

# 4. Security Knowledge Base

The production-oriented security KB lives under:

```text
knowledge_base/security
```

It covers:

- review evidence policy and false-positive handling;
- secrets and credentials;
- authentication/session/token security;
- authorization and access control;
- SQL/command injection, traversal, SSRF, file handling;
- API security, sensitive data, cryptography;
- supply chain, configuration, logging, errors;
- AI / LLM / tool security.

## Key design principle

A keyword alone should not create a security finding.

Examples:

```text
SECRET_KEY in detector code      != production secret
DEBUG in a rule definition       != debug mode enabled
LLM tokenizer token              != authentication token
admin in documentation           != hardcoded admin credentials
```

This knowledge is especially useful for the contextual OpenAI reviewer.

The deterministic reviewer remains intentionally simple and pattern-based.

---

# 5. Review Engine

AgentLoop supports two reviewer modes.

## 5.1 Deterministic Reviewer

Strengths:

- fast;
- cheap;
- reproducible;
- CI-friendly;
- easy to test;
- no external source-code processing.

Weaknesses:

- limited semantic context;
- pattern matching can produce false positives;
- terminology can be mistaken for actual behavior.

Best use:

```text
broad baseline scan
```

---

## 5.2 OpenAI Reviewer

Strengths:

- contextual reasoning;
- can distinguish vocabulary from execution semantics;
- can use retrieved security policy;
- better for ambiguous findings.

Weaknesses:

- slower;
- cost;
- external processing boundary;
- prompt-injection surface;
- large reviews can exceed MCP tool timeout.

Best use:

```text
targeted contextual follow-up
```

---

# 6. Final Security Experiment

One of the strongest demonstrations in the project was the difference between deterministic and contextual review.

## Deterministic baseline

A large `main...dev` review produced approximately:

```text
265 changed files
95 reviewed Python files
6 findings
```

Several findings were lexical false positives in AgentLoop's own security/retrieval code.

Examples included terminology around:

```text
SECRET_KEY
DEBUG
admin
token
```

## Contextual OpenAI + Security KB

A targeted small diff was then reviewed using the OpenAI reviewer and the production security KB.

Result:

```text
9 changed files
4 reviewed files
2 findings
MEDIUM x 2
```

The old lexical false positives disappeared.

Instead, the reviewer identified two more realistic architectural concerns:

1. source code is sent to an external LLM service without an explicit redaction/data-classification boundary;
2. untrusted source-file content is embedded into reviewer instructions, creating a prompt-injection risk.

This is the project's best example of:

```text
deterministic detection
        +
retrieved domain policy
        +
contextual LLM reasoning
        =
better semantic review quality
```

---

# 7. Git-Aware Review

AgentLoop can review:

```text
Workspace
Git ref diff
Staged Git index
```

## PR-style branch review

Uses triple-dot semantics:

```text
base...target
```

For a feature branch `dev` merging into `main`:

```text
base_ref = main
target_ref = dev
```

Git is used primarily as a **scope selector**.

The review engine itself is reused.

## Staged review

Important implementation detail:

```text
git diff --cached
```

selects the files.

The reviewed content is read from the **Git index snapshot**, not the working tree.

This avoids a subtle bug where unstaged local edits could contaminate a staged-code review.

This is a good interview detail because it demonstrates attention to real Git semantics rather than only building a UI around `git diff`.

---

# 8. MCP Architecture

AgentLoop exposes a local MCP server over stdio.

Conceptually:

```text
VS Code / Copilot Agent
          |
          v
     MCP Protocol
          |
          v
 AgentLoop MCP Server
          |
          v
 Product Workflows
          |
          v
 Existing Review Runtime
```

MCP is an adapter, not a separate implementation of review logic.

This avoids architecture such as:

```text
CLI reviewer
MCP reviewer
Web reviewer
```

with duplicated logic.

Instead:

```text
                Shared review workflows
                  /       |       \
                 /        |        \
               CLI       MCP      Web UI
```

This is a strong design decision to mention in interviews.

---

# 9. Web UI

The Web UI is intentionally lightweight.

Technology:

```text
Python standard library HTTP server
HTML
CSS
JavaScript
```

No React, Node, or separate frontend build pipeline was introduced.

The UI acts as a local adapter over the same review workflows.

Supported operations:

- workspace review;
- Git diff review;
- staged review;
- reviewer/preset selection;
- recent history;
- opening generated HTML reports.

The decision was deliberate: the project goal was agentic architecture, not frontend complexity.

---

# 10. Persistent Review Artifacts

Each review creates a run package similar to:

```text
reviews/
  history.json

  <run_id>/
    report.md
    report.html
    summary.json
    findings.json
    reviewed_files.json
    run_config.json
```

Comparison artifacts are stored separately:

```text
reviews/
  comparisons/
    <comparison_id>/
      comparison.json
      comparison.md
      comparison.html
```

Why this matters:

- reproducibility;
- auditability;
- review history;
- debugging;
- comparing deterministic vs LLM runs;
- future CI or dashboard integration.

---

# 11. Stable Finding Identity

LLM wording is unstable.

Two equivalent findings may be phrased differently:

```text
"Token validation is incomplete."

vs.

"Bearer token claims are trusted without cryptographic verification."
```

Text equality therefore does not work well for run comparison.

AgentLoop introduced stable finding types such as:

```text
security.hardcoded_secret
security.hardcoded_admin_credentials
security.debug_mode
security.token_validation
security.token_expiration
security.information_disclosure
security.other
```

Comparison can then classify:

```text
new
resolved
unchanged
severity changed
```

without depending on exact natural-language wording.

This is a useful example of converting probabilistic LLM output into a more deterministic product model.

---

# 12. Configuration Architecture

Non-secret runtime settings are centralized in:

```text
agentloop.toml
```

Examples:

- model;
- output-token limits;
- request timeouts;
- command timeout;
- agent step limits;
- rejection limits;
- review limits;
- RAG chunking/retrieval defaults;
- workspace presets;
- artifact directories.

Secrets remain environment-based:

```text
OPENAI_API_KEY
```

General precedence:

```text
Explicit argument
      >
Environment variable
      >
agentloop.toml
      >
Built-in fallback
```

This avoided scattering runtime constants throughout the codebase.

---

# 13. Evaluation Strategy

AgentLoop does not rely only on manual demos.

The evaluation suite covers:

```text
retrieval
answer
grounding
agent behavior
```

Typical final output:

```text
overall: passed
retrieval: passed
answer: passed
grounding: passed
agent: passed
```

The important engineering lesson:

> Agent/RAG changes need regression tests and measurable evaluation just like conventional software.

Examples of evaluation questions:

- Was the correct source retrieved?
- Was it ranked highly enough?
- Was the answer grounded in retrieved evidence?
- Did the agent use the expected tools?
- Did it inspect required files?
- Did it stop correctly?
- Did it produce the expected type of finding?

---

# 14. Key Design Decisions and Trade-Offs

## Decision 1 — Build the loop rather than start with a framework

Reason:

```text
Learn mechanics first:
state
tools
observations
guardrails
failure modes
```

Trade-off:

More implementation work, but much deeper understanding.

---

## Decision 2 — Keep deterministic controls outside the LLM

Examples:

- path safety;
- Git scope;
- tool contracts;
- max steps;
- file-size limits;
- artifact creation;
- finding normalization;
- configuration limits.

Reason:

These operations require predictable behavior.

---

## Decision 3 — Deterministic + LLM reviewers instead of LLM-only

Reason:

Different workloads need different trade-offs.

```text
Deterministic = high reproducibility / lower semantic quality
LLM           = higher semantic quality / higher cost and latency
```

Together they form a more practical architecture.

---

## Decision 4 — RAG policy instead of putting all security knowledge in the system prompt

Reason:

- modular;
- updateable;
- traceable;
- source-aware;
- easier to evaluate;
- can support multiple policy domains later.

---

## Decision 5 — Reuse review workflows across interfaces

Adapters:

```text
CLI
MCP
Web UI
```

all use the same underlying review logic.

Reason:

Avoid duplicated business logic and behavioral drift.

---

## Decision 6 — Git selects scope; review engine remains generic

Reason:

Avoid building a separate PR review engine.

Git-specific code answers:

```text
What files/content should be reviewed?
```

The review engine answers:

```text
What issues exist?
```

Good separation of concerns.

---

# 15. Known Limitations

These should be stated confidently in an interview rather than hidden.

## Deterministic review

- regex/pattern oriented;
- lexical false positives;
- limited cross-file context.

## OpenAI review

- source code may leave the local process;
- prompt-injection surface from reviewed content;
- slower than deterministic review;
- large sequential reviews can exceed MCP host timeout.

## Scalability

- local filesystem artifacts;
- no background workers;
- no distributed queue;
- no large-scale concurrent LLM orchestration.

## Product completeness

- no multi-user authorization;
- no GitHub/GitLab API integration;
- no automated finding suppression lifecycle;
- no full repository policy-management UI;
- no changed-hunk-only semantic review.

These are roadmap items, not evidence the prototype failed.

---

# 16. Future Roadmap

A credible next-generation roadmap would be:

1. **Sensitive-data policy before external LLM calls**
   - secret classification;
   - redaction;
   - repository policy;
   - provider/privacy controls.

2. **Prompt-injection isolation**
   - trusted instructions separated from code;
   - explicit untrusted-data boundaries;
   - output validation.

3. **Scalable LLM review**
   - batching;
   - bounded parallelism;
   - async/background jobs;
   - resumable reviews.

4. **PR platform integration**
   - GitHub/GitLab APIs;
   - inline comments;
   - status checks.

5. **Finding lifecycle**
   - accepted;
   - suppressed;
   - false positive;
   - fixed;
   - baseline management.

6. **Changed-hunk-aware semantic review**
   - analyze modified code rather than complete changed files when appropriate.

---

# 17. 30-Second Interview Pitch

> I built AgentLoop to understand agentic engineering from the mechanics upward rather than only using a framework. It started as a custom tool-using agent with state, guardrails and structured outputs, and evolved into an engineering review platform with RAG, evaluation, deterministic and LLM reviewers, MCP integration, Git-diff and staged review, persistent artifacts and a local Web UI. A key design principle was keeping deterministic controls in application code and using the LLM only where semantic reasoning adds value.

---

# 18. 90-Second Interview Pitch

> I started AgentLoop from the basic agent loop itself: state, tool calls, observations, structured outputs, guardrails and stop conditions. Then I added a custom RAG pipeline with multiple retrieval strategies, provenance, persistent indexing and automated evaluation for retrieval, answer quality and grounding.
>
> I then turned it into a practical engineering workflow. I exposed it through MCP so it can be called directly from VS Code, added deterministic and OpenAI-based reviewers, stable finding identities, persistent run artifacts and comparison between review runs.
>
> The latest version can review an entire workspace, a Git diff between branches or commits, or exactly what is staged in the Git index. It also has a lightweight local Web UI.
>
> One useful experiment compared the deterministic scanner against an LLM reviewer backed by a production-oriented security knowledge base. The deterministic scanner produced lexical false positives around words such as SECRET_KEY and token. The contextual reviewer removed those and instead identified more realistic architectural concerns around external source-code processing and prompt injection.
>
> The main lesson was that good agentic systems are not about maximizing LLM autonomy. They are about deciding carefully what should be probabilistic and what should remain deterministic.

---

# 19. Deep-Dive Interview Questions

## Q: Why did you build your own agent loop instead of LangChain/LangGraph?

Good answer:

> The main purpose was to understand the mechanics directly: state transitions, tool schemas, observation handling, invalid model output, guardrails, termination and traceability. A framework can still be useful later, but building the loop made failure modes and architectural boundaries much clearer.

---

## Q: What makes AgentLoop agentic rather than just an LLM call?

Answer:

> The model participates in an iterative stateful loop. It can choose tools, inspect observations, perform multiple retrieval steps, add findings, and decide when it has enough evidence to finish. Application-side guardrails constrain which actions are valid and when finalization is allowed.

---

## Q: What is agentic RAG in your implementation?

Answer:

> Instead of one fixed retrieval call followed by generation, the agent can perform multiple knowledge searches, inspect evidence from each query, decide whether more evidence is needed, and only then compose the answer. The retrieved evidence and provenance remain part of the state.

---

## Q: How do you prevent hallucinated findings?

Answer:

> I do not assume hallucinations can be eliminated completely. I reduce them with evidence requirements, security policy retrieval, structured finding schemas, deterministic validation, scoped source access, and explicit instructions that every finding must be supported by concrete file evidence. The final result still requires engineering judgment.

---

## Q: Why keep a deterministic reviewer?

Answer:

> Reproducibility and cost. A deterministic scanner is fast, testable and useful as a baseline. The LLM reviewer adds semantic context where the deterministic rules are weak. They solve different parts of the problem.

---

## Q: How do you compare LLM review runs when wording changes?

Answer:

> Findings are normalized into stable finding types such as security.token_validation or security.hardcoded_secret. Run comparison uses those stable identities rather than exact issue wording.

---

## Q: Why use RAG for security policies?

Answer:

> It lets security knowledge evolve independently from the review engine. It also gives source provenance, allows retrieval to be evaluated separately, and avoids continuously expanding one huge prompt.

---

## Q: What was a real RAG failure you observed?

Answer:

> A term-frequency retriever could rank a document containing repeated occurrences of one query word above a document that covered all query concepts. That led me to compare retrieval strategies and build explicit evaluation cases instead of trusting intuitive retrieval behavior.

---

## Q: How does staged review avoid reading unstaged edits?

Answer:

> The Git index is treated as the source of truth. The file list comes from the cached diff and the file content is read from the staged snapshot, not from the working tree.

---

## Q: What is the most important security concern in AgentLoop itself?

Answer:

> The OpenAI reviewer introduces a data boundary because source code can be sent to an external service. There is also a prompt-injection boundary because reviewed source text is untrusted model input. Those are explicit roadmap items: classification/redaction, provider policy, stronger trusted/untrusted prompt separation and deterministic output validation.

---

## Q: What would you change to handle 1,000 files?

Answer:

> I would not send 1,000 full files sequentially. I would first reduce scope through Git/hunk selection and deterministic filtering, then use bounded parallelism or background workers for contextual review. I would also cache unchanged analysis, implement resumable jobs and separate orchestration from synchronous MCP request lifetime.

---

# 20. Senior/Director-Level Discussion

For a senior engineering leadership interview, avoid presenting AgentLoop only as a coding exercise.

Emphasize the architecture choices:

```text
prototype -> product workflow
deterministic + probabilistic components
evaluation instead of demos
shared runtime across interfaces
operational limits
security boundaries
Git workflow integration
artifact/audit model
future scalability path
```

A useful framing:

> I used the project to explore not only how to call an LLM, but how to make LLM behavior fit into a conventional software-engineering system with deterministic controls, contracts, evaluation, persistence and operational boundaries.

This maps well to engineering leadership because the important challenge in AI adoption is usually not model invocation. It is building reliable systems and development processes around probabilistic components.

---

# 21. CTO-Level Discussion

At CTO level, frame the project around technology strategy.

Key points:

- do not replace deterministic software with LLMs unnecessarily;
- identify where reasoning provides economic value;
- build evaluation before scaling AI adoption;
- preserve auditability and data boundaries;
- separate model/provider choice from application architecture;
- design fallbacks and bounded failure modes;
- control cost/latency by reducing semantic-review scope;
- enable integration through stable protocols such as MCP;
- treat proprietary-code transmission as a governance decision, not only an implementation detail.

Good CTO-level statement:

> AgentLoop reinforced my view that AI-native architecture should not mean LLM-everywhere architecture. The strongest systems combine conventional deterministic software with narrowly scoped probabilistic reasoning, measurable evaluation, explicit trust boundaries and replaceable model providers.

---

# 22. CV / LinkedIn Bullet Options

## Technical / hands-on

> Designed and implemented AgentLoop, an agentic engineering review platform with custom tool-use loops and guardrails, multi-step RAG, deterministic and LLM reviewers, evaluation pipelines, MCP integration, Git-diff/staged review, persistent artifacts, and a local Web UI.

## Senior engineering leader

> Built an AI-assisted engineering review platform combining deterministic and LLM-based code analysis, RAG-backed security policies, automated evaluation, Git-aware workflows, MCP/VS Code integration, and persistent review history.

## Short version

> Built an agentic code-review prototype combining RAG, LLM reasoning, deterministic controls, MCP, Git-aware review, and automated evaluation.

---

# 23. Concepts to Be Ready to Explain

Before an interview, be comfortable explaining these without notes:

```text
agent loop
state
tool call
observation
guardrail
structured output
tool contract
RAG
chunking
retrieval strategy
provenance
grounding
agentic RAG
evaluation
false positive / false negative
stable finding identity
MCP
stdio transport
Git triple-dot diff
Git index snapshot
deterministic vs probabilistic component
prompt injection
external-processing boundary
bounded parallelism
```

---

# 24. Final Project Positioning

Do not position AgentLoop as:

```text
"an enterprise security product"
```

A better description is:

```text
engineering-grade prototype
production-oriented prototype
agentic engineering review platform prototype
```

The project is strong because it demonstrates a complete engineering path:

```text
agent mechanics
    ->
RAG
    ->
evaluation
    ->
tool protocol
    ->
product workflows
    ->
Git integration
    ->
persistent artifacts
    ->
UI
    ->
security knowledge
    ->
real architectural limitations
```

That journey is more valuable in an interview than claiming that the current prototype is a finished commercial product.

---

# 25. The Main Lesson

The most important technical conclusion from AgentLoop is:

> **Reliable agentic systems are built by combining probabilistic reasoning with deterministic software boundaries, measurable evaluation, explicit trust models, and conventional engineering discipline.**

That is the central architectural idea to carry from the project into future AI systems.
