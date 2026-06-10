# Session Logs

This directory archives chat session logs from the SDD (Spec-Driven Development) process.

## Purpose

Per the CONSTITUTION Section VIII (Human-in-the-Loop), point 4:

> Chat logs documenting the SDD process SHOULD be archived in `docs/sessions/` for auditability.

Each session is stored in its own subdirectory named by task ID.

## Structure

```
docs/sessions/
├── README.md              # This file
└── <task-id>/             # One directory per session
    ├── api_conversation_history.json
    ├── context_history.json
    ├── focus_chain_taskid_<task-id>.md
    ├── task_metadata.json
    └── ui_messages.json
```

## Usage

- **Read-only archive.** These files are not modified after the session ends.
- **Audit trail.** They provide a complete record of automated tooling actions and human confirmations during the SDD lifecycle.
- **Not committed by default.** Sessions are typically excluded from version control unless needed for compliance or review.

## Adding New Sessions

When a new SDD session completes, export the chat logs and place them in a new subdirectory named after the session's task ID:

```
docs/sessions/<task-id>/