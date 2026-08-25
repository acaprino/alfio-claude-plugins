---
name: review-orchestrator
description: Copilot-specific orchestrator for the example review workflow.
tools: ['agent']
agents: ['inspector']
---

# Review orchestrator

Dispatch one `inspector` per selected scope. Each inspector runs in its own context and never reads
another inspector's result. Wait for every inspector to deliver, then return the declared result
contract.
