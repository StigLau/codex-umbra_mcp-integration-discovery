# Codex Umbra: Component - The Visage

## Component Name
The Visage

## Role
User-facing element of Codex Umbra. Provides a responsive and interactive chat environment for users to communicate with The Oracle.

## Technology
- React
- TypeScript
- Vite (build tool and development server)

## Scaffolding with Vite
- Requires Node.js version 18+ or 20+.
- Command: `npm create vite@latest codex-umbra-visage -- --template react-ts`
  (Or `yarn`/`pnpm` equivalents).
- This sets up a project with React, TypeScript, and Vite's default configurations.
- Further TypeScript configuration (`tsconfig.json`, etc.) may be needed.

## Project Structure Recommendation
- Component-centric file structure: Files related to a specific component (logic, styles, tests, assets) are grouped in a dedicated folder.
- Example:
  ```
  src/
  ├── components/
  │   ├── ChatInput/
  │   │   ├── ChatInput.tsx
  │   │   ├── ChatInput.module.css
  │   │   └── ChatInput.test.tsx
  │   └── MessageList/
  │       ├── MessageList.tsx
  │       └── MessageList.module.css
  ├── App.tsx
  └── main.tsx
  ```
- Enforce consistent naming conventions (e.g., PascalCase for components).
