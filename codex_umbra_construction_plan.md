# Codex Umbra: Recommended Construction Plan

This document outlines a recommended phased approach for building the Codex Umbra project, ensuring a structured development process from foundational setup to integrated system.

## Phase 0: Prerequisites and Environment Setup

1.  **Install Core Technologies:**
    *   **Python:** Ensure a recent version of Python is installed for The Conductor and The Sentinel.
    *   **Node.js:** Install Node.js (version 18+ or 20+) for The Visage.
    *   **Ollama:** Install Ollama on your development machine.
        *   Refer to `codex_umbra_component_oracle.md` for installation instructions (e.g., `sudo dnf install ollama` or download from the official site).
2.  **Set Up The Oracle (Mistral LLM):**
    *   Pull the Mistral model: `ollama pull mistral`
    *   Verify Mistral is runnable: `ollama run mistral`
    *   Note any custom model storage if `OLLAMA_MODELS` is set.
3.  **Version Control:**
    *   Initialize a Git repository for the project if not already done.
    *   Establish a branching strategy (e.g., git-flow).

## Phase 1: Develop The Sentinel (MCP Server) - The Foundation

*Goal: Create a functional internal system API that The Conductor can interact with.*

1.  **Project Scaffolding (Python/FastAPI):**
    *   Create the `mcp_server_project` directory.
    *   Set up a Python virtual environment.
    *   Install FastAPI and Uvicorn: `pip install fastapi uvicorn[standard]`
    *   Implement the basic FastAPI application structure as outlined in `codex_umbra_component_sentinel.md`.
2.  **Implement Core Endpoints:**
    *   **`/status` endpoint:** As per `codex_umbra_component_sentinel.md`.
    *   **`/health` endpoint:** Implement the health check mechanism as detailed in `codex_umbra_component_sentinel.md` and `codex_umbra_testing_strategy.md`. This is crucial for monitoring.
    *   Define 1-2 basic functional endpoints that represent core MCP actions (e.g., get system data, set a parameter). Keep these simple initially.
3.  **Initial Unit Tests:**
    *   Write `pytest` unit tests for the implemented endpoints, especially `/health` and `/status`.
4.  **Documentation:**
    *   Start documenting The Sentinel's API endpoints (e.g., using FastAPI's automatic OpenAPI/Swagger docs).

## Phase 2: Develop The Conductor (Backend Orchestrator) - The Brain

*Goal: Create the central orchestrator that can communicate with The Sentinel and prepare for LLM interaction.*

1.  **Project Scaffolding (Python/FastAPI):**
    *   Create the `conductor_project` directory.
    *   Set up a Python virtual environment.
    *   Install FastAPI and Uvicorn: `pip install fastapi uvicorn[standard]`
    *   Implement the basic FastAPI application structure as per `codex_umbra_component_conductor.md`.
2.  **Implement Sentinel Communication Service:**
    *   Create a service module within The Conductor to make HTTP requests to The Sentinel's API.
    *   Implement functions to call The Sentinel's `/status`, `/health`, and the basic functional endpoints created in Phase 1.
    *   Handle responses and errors from The Sentinel.
3.  **Basic API Endpoints for The Visage:**
    *   Define initial API endpoints in The Conductor that The Visage will eventually call (e.g., `/api/v1/chat`). For now, these can return placeholder responses or directly trigger calls to The Sentinel.
4.  **Initial LLM Interaction Service (Placeholder/Basic):**
    *   Create a service module for interacting with The Oracle (Ollama/Mistral).
    *   Implement a basic function to send a hardcoded prompt to Ollama's API (Ollama serves an API, typically on `http://localhost:11434/api/generate` for streaming or `http://localhost:11434/api/chat` for chat completions). You'll need an HTTP client library like `requests` or `httpx`.
    *   `pip install httpx`
    *   Focus on establishing connectivity and getting a response.
5.  **Unit and Integration Tests:**
    *   Write `pytest` unit tests for The Conductor's services.
    *   Write basic integration tests for Conductor <-> Sentinel communication.

## Phase 3: Develop The Visage (Web Interface) - The Face

*Goal: Create a basic user interface to send messages and display responses.*

1.  **Project Scaffolding (React/TypeScript/Vite):**
    *   Create the `codex-umbra-visage` project using Vite: `npm create vite@latest codex-umbra-visage -- --template react-ts`
    *   Set up the project structure as recommended in `codex_umbra_component_visage.md`.
2.  **Implement Basic UI Components:**
    *   `ChatInput` component: A text field and a send button.
    *   `MessageList` component: To display messages (user inputs and system responses).
    *   Basic `App.tsx` to assemble these components.
3.  **API Communication Service:**
    *   Implement functions (e.g., using `fetch` or `axios`) to send user messages from `ChatInput` to The Conductor's API endpoint (`/api/v1/chat`).
    *   Handle responses from The Conductor and display them in `MessageList`.
4.  **State Management:**
    *   Implement basic state management (e.g., React Context or a simple state library) to handle messages and application state.
5.  **Unit Tests:**
    *   Write basic unit tests for React components using Jest/Vitest.

## Phase 4: Integration and Core Workflow (Architect Mode - Initial)

*Goal: Achieve a basic end-to-end flow: User input in Visage -> Conductor -> Oracle -> Conductor -> Sentinel (optional initially) -> Conductor -> Visage response.*

1.  **Connect Visage to Conductor:**
    *   Ensure The Visage can successfully send messages to The Conductor and display its responses.
2.  **Full Conductor-Oracle Integration:**
    *   Refine The Conductor's LLM service to:
        *   Take user input received from The Visage.
        *   Formulate a basic prompt using this input (refer to "General User Request Interpretation" in `codex_umbra_llm_guidelines.md`).
        *   Send the prompt to The Oracle (Mistral via Ollama API).
        *   Receive and parse The Oracle's response.
3.  **Initial Conductor-Sentinel Command Execution (Optional but Recommended):**
    *   Based on a very simple, structured response from The Oracle (e.g., if Oracle says "get_status"), have The Conductor call the corresponding Sentinel endpoint.
    *   Return the result from The Sentinel (or a summary) back to The Visage.
4.  **End-to-End Testing:**
    *   Manually test the full flow.
    *   Begin scripting E2E tests (Cypress/Playwright) for simple scenarios.
    *   Refer to `codex_umbra_testing_strategy.md` for E2E and integration testing guidelines.
5.  **Logging:**
    *   Implement basic logging in The Conductor, especially for interactions with The Oracle and The Sentinel.

## Phase 5: Refinement and Feature Expansion (Architect/Running Mode)

*Goal: Enhance LLM interaction, expand Sentinel capabilities, and improve user experience.*

1.  **Advanced LLM Prompting (Architect Mode):**
    *   Implement "Discovery Phase Prompts" (`codex_umbra_llm_guidelines.md`) to teach The Oracle about The Sentinel's API. This might involve The Conductor sending API docs or structured descriptions to The Oracle.
    *   Refine "User Interaction & Command Interpretation Prompts" based on testing.
    *   Focus on structured output from The Oracle (JSON).
2.  **Expand Sentinel Functionality:**
    *   Add more complex API endpoints to The Sentinel based on project requirements.
    *   Update The Oracle's knowledge of these new capabilities.
3.  **Enhance Conductor Logic:**
    *   Improve parsing of The Oracle's structured responses.
    *   Implement more robust mapping of Oracle outputs to Sentinel commands.
    *   Handle missing parameters and clarification dialogues as per `codex_umbra_llm_guidelines.md`.
4.  **Improve Visage UI/UX:**
    *   Add features like chat history, loading indicators, error message display.
5.  **Comprehensive Testing:**
    *   Expand unit, integration, and E2E test suites to cover new features.
    *   Pay close attention to the "Unit Test Mandate" in `codex_umbra_testing_strategy.md`.

## Phase 6: Towards "In the Wild" and Future Augmentations

*Goal: Stabilize the system and explore advanced features.*

1.  **Robustness and Scalability:**
    *   Optimize performance of all components.
    *   Enhance error handling and resilience.
2.  **Security:**
    *   Implement security best practices (input validation, sanitization, authentication/authorization if needed). Refer to "Future Security Considerations" in `codex_umbra_testing_strategy.md`.
3.  **Self-Modification Protocol (TODO - Long-term):**
    *   Begin research and design for the self-modification capabilities outlined in `codex_umbra_component_conductor.md` under "Future Augmentations." This is a significant R&D effort.

## Ongoing Activities (Throughout All Phases)

*   **Adhere to Prime Directive:** Continuously ensure code is concise, efficient, and maintainable.
*   **Documentation:** Keep all project documentation (`*.md` files, API docs, code comments) up-to-date.
*   **Version Control:** Commit frequently with clear messages. Use branches for features and fixes.
*   **Regular Testing:** Run tests frequently to catch regressions early.
*   **Iterative Refinement:** Be prepared to revisit and refine components as the project evolves.

This plan provides a structured path, but remember that software development is often iterative. Be flexible and adapt as you learn more and as project requirements evolve.
