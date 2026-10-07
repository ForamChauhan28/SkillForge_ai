---
description: Enforces the Project Mind Map Protocol for context optimization and agent-managed synchronization.
---

# Project Mind Map Protocol

You are equipped with the **Project Mind Map Protocol** architectural skill. Your goal is to conserve context window tokens, eliminate redundant file reading, and maintain a high-level semantic index of this project in a single YAML file (`.antigravity_map.yaml`) at the root directory.

## Strict Operating Protocols

### 1. The "Read-First" Protocol (Context Optimization)
* **Never** scan or read the entire codebase when asked an architectural, debugging, or feature-planning question.
* **Always** read `.antigravity_map.yaml` first.
* Identify the exact file path(s) relevant to the user's request from the YAML map, and **only read those specific files**.
* If `.antigravity_map.yaml` does not exist in the root directory, immediately generate it by scanning the project's existing structure before proceeding with any user request.

### 2. The "Update-on-Write" Protocol (Agent-Managed Synchronization)
* Whenever you **create a new file**, **delete a file**, or **significantly refactor an existing file**, you are strictly required to update `.antigravity_map.yaml` as part of your task completion.
* Update the file summary in `.antigravity_map.yaml` to reflect the current state of the project before presenting your final answer or artifact to the user.
* Do not ask the user for permission to update the map; maintain it silently and autonomously in parallel with development.

## The YAML Schema Standard (`.antigravity_map.yaml`)

Whenever you create or update the mind map, you MUST adhere strictly to the following YAML schema structure:

```yaml
project_name: "String (Name of the project or workspace)"
last_updated: "YYYY-MM-DD"
overview: "One-sentence high-level summary of the project architecture."

modules:
  - path: "relative/path/to/file.ext"
    purpose: "One-sentence explanation of what this file is responsible for."
    exports:
      - "MainClassOrFunction1"
      - "MainClassOrFunction2"
    dependencies:
      - "relative/path/to/dependency.ext"
```
