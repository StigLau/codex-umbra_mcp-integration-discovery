# Codex Umbra: Project Summary

## Project Name
Codex Umbra

## Core Mandate
To develop an advanced, evolving chat interface that serves as a sophisticated bridge between users and an internal system (The Sentinel - MCP Server). This interaction is mediated by the Mistral Large Language Model (LLM), running locally via Ollama. The system is designed to be evolutionary.

## Prime Directive for LLM Construct
All code must be:
- **Concise:** As short and to the point as possible without sacrificing clarity or functionality.
- **Efficient:** Optimized for speed and resource utilization.
- **Maintainable:** Well-structured, clearly documented, and easy to understand, modify, and extend.

## System Architecture Components
1.  **The Oracle (Mistral on Ollama):** AI core; interprets inputs, generates responses/commands.
2.  **The Visage (React/TypeScript Web Interface):** User-facing chat environment.
3.  **The Conductor (Python Backend Orchestrator - FastAPI):** Central nervous system; manages communication flow, processes commands, interacts with The Sentinel.
4.  **The Sentinel (Python MCP Server Sub-Project - FastAPI):** Internal system with an API for control and data retrieval.

## Operational Modes
1.  **Architect Mode:** Learning, configuration, defining operational parameters.
2.  **Running Mode:** Standard operational mode for user interaction with The Sentinel.
3.  **In the Wild Mode:** Future aspiration for more autonomous behaviors.
