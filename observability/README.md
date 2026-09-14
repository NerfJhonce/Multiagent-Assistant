# Observability & Tracing Configuration

## Overview
This directory manages the observability and tracing setup for the Multi-Agent Assistant using **Langfuse**.

## How It Works
1. The Orchestrator initializes the `CallbackHandler` from `langfuse.langchain`.
2. Traces are automatically generated for every state transition in LangGraph (`Planner` → `Researcher` → `Developer` → `Tester` → `Reviewer`).
3. LLM prompts, token consumption, node latency, and execution failures are captured end-to-end.

## Environment Variables
Ensure the following keys are set in your `.env` or Docker Compose environment for the Orchestrator service:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=[https://cloud.langfuse.com](https://cloud.langfuse.com) # or http://localhost:3000 for self-hosted