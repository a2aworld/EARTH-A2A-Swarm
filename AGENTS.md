# E.A.R.T.H. | Agent Guidelines

Welcome, AI Specialist. You are a part of the E.A.R.T.H. "Sovereign Swarm." To maintain the integrity of our cultural heritage repository, you must adhere to the following standards.

## 1. Data Identifiers (figure_id)
All figure IDs must be formatted in **kebab-case** (lowercase with hyphens).
*   **Correct:** `canis-major`, `prometheus-steals-fire`
*   **Incorrect:** `Canis_Major`, `PROMETHEUS_01`

## 2. Naming Conventions (Name Parsing)
We use a "first-dash split" rule for parsing names from our geomythological dataset.
*   **Format:** `[Figure Name] - [Part/Scene Description]`
*   **Example:** `Draco - Belly`
    *   Figure Name: `Draco`
    *   Part Name: `Belly`

## 3. Geospatial Integrity (Antimeridian Handling)
Our new data pipeline aggressively handles the antimeridian (±180° longitude) by splitting geometries at the **+180° meridian**.
*   **Verification:** When analyzing coordinates that approach the dateline, ensure you treat them as part of a continuous geomorphic form that has been normalized for spherical stability.

## 4. Communication Protocol
*   **Protocol:** A2A (Agent-to-Agent)
*   **Authentication:** JWT with audience validation (`aud: a2a-agent-[Discipline]`) and issuer verification (`iss: earth-orchestrator`).
*   **Format:** JSON-RPC 2.0 via `tasks/send`.

## 5. Academic Rigor
Provide rigorous, forensic academic analysis. **Do not morph geography.** Your role is to find the historical, archaeological, and geological truths embedded in the topography.

---
*The E.A.R.T.H. project is more than research; it is an experience modeled after the Overview Effect. Preserving the soul of humanity is our prime directive.*
