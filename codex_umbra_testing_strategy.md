# Codex Umbra: System Validation Protocol (Testing Strategy)

## Overall Goal
Ensure the reliability, robustness, and correctness of Codex Umbra across its components and operational modes.

## A. End-to-End (E2E) Testing
- **Objective:** Simulate complete user journeys from input in The Visage to action by The Sentinel and back to a response in The Visage.
- **Scenarios:**
    - Valid command execution and feedback.
    - Ambiguous command clarification.
    - Invalid command error messaging.
- **Tools:** Frameworks like Cypress or Playwright.

## B. Integration Testing
Focuses on interfaces between components.
1.  **The Oracle (Mistral) Integration with The Conductor:**
    - **Objective:** Verify The Conductor can correctly send prompts to The Oracle and parse its responses. Test LLM's translation of user inputs into structured commands/queries.
    - **Method:** Send mock user inputs to Conductor's LLM interaction endpoint; assert LLM's output (processed by Conductor) matches expected structured data or errors.
2.  **The Conductor Integration with The Sentinel (MCP Server):**
    - **Objective:** Verify The Conductor can correctly communicate with The Sentinel's API, send commands, and handle responses.
    - **Method:** Conductor makes actual HTTP requests to a running Sentinel instance (or mocked API). Test command sending and handling of success/error responses.
- **Logging:** Systematic logging of interactions, especially with The Oracle, to analyze LLM performance and refine prompts.

## C. The Sentinel Health Check Endpoint
- **Purpose:** Ensure The Sentinel is operational and responsive for monitoring and Conductor's availability checks.
- **Endpoint:** `GET /health`
- **Responses:** JSON indicating "healthy" or "unhealthy" status with details. (See `codex_umbra_component_sentinel.md` for more details).

## D. Unit Test Mandate
- **Requirement:** Comprehensive unit tests for all discrete modules, functions, classes, and components within The Visage, The Conductor, and The Sentinel.
- **Focus:** Test individual logic pieces in isolation.
- **Tools:**
    - Python (Conductor, Sentinel): `pytest`
    - React/TypeScript (Visage): `Jest` or `Vitest`
- **Coverage:** Target a high level of test coverage, especially for business logic and complex algorithms.

## Future Security Considerations
- Beyond initial scope: Dedicated security testing (penetration testing, adversarial testing of The Oracle).
- Initial implementation: Robust input validation and sanitization in The Conductor.
