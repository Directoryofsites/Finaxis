# CRITICAL AGENT RULES

This file contains absolute rules that must be followed by any AI agent (Antigravity, Kyro, etc.) working on this repository to maintain strict environment isolation.

## 1. Environment Configuration (.env)

**Rule:** The `.env` file is strictly **LOCAL-ONLY**.

*   **NEVER** track `.env` in git.
*   **NEVER** run `git add .env`.
*   **NEVER** run `git add .` without verifying that `.env` is ignored.
*   **ALWAYS** ensure `.env` is listed in `.gitignore`.

**Reasoning:**
We maintain two distinct development environments:
1.  **Kyro's Environment:** Uses `kiro_clean_db` (Port 8002).
2.  **Antigravity's Environment:** Uses `contapy_db` (Port 8000).

Tracking `.env` causes immediate conflict and overwrites the local configuration of the other agent, breaking access.

## 2. Database Independence

*   Agents should only connect to their designated database unless explicitly instructed to migrate data.
*   **Antigravity** -> `contapy_db`
*   **Kyro** -> `kiro_clean_db`
