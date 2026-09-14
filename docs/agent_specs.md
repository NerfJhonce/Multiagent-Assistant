# Agent Specifications

## 1. Orchestrator
- **Purpose:** Manages system workflow state, routes requests between specialized agent nodes, and terminates loop execution upon task completion.
- **Inputs:** User Task string.
- **Outputs:** Final execution status, output artifact, and execution trace.
- **Tools:** Router, LangGraph State Engine.

## 2. Planner Agent
- **Purpose:** Deconstructs complex user tasks into a clear, sequential implementation plan.
- **Inputs:** Raw User Task, project context.
- **Outputs:** JSON structured execution steps.
- **Tools:** LLM Engine.
- **Success Criteria:** Clear step-by-step breakdown without ambiguities.

## 3. Researcher Agent
- **Purpose:** Gathers framework-specific knowledge, syntaxes, and technical documentation.
- **Inputs:** Task specification, plan requirements.
- **Outputs:** Technical context and code guidelines.
- **Tools:** Knowledge Base / Search API.

## 4. Developer Agent
- **Purpose:** Writes clean, modular, and functional code based on plans and research.
- **Inputs:** Implementation plan, technical guidelines, reviewer feedback (if iterative).
- **Outputs:** Production-ready source code.
- **Tools:** Code Generator, Sandbox File Operations.
- **Constraints:** Must not access host system outside designated workspace.

## 5. Reviewer Agent
- **Purpose:** Analyzes proposed code for bugs, architectural adherence, and security flaws.
- **Inputs:** Source code, task plan.
- **Outputs:** Structural feedback and approval flag (`approved: true/false`).

## 6. Tester Agent
- **Purpose:** Generates unit tests and validates execution within the isolated sandbox.
- **Inputs:** Source code, testing criteria.
- **Outputs:** Test suites, execution logs, pass/fail status.
- **Tools:** Pytest Runner, Docker Sandbox.