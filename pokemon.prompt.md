# Prompt: Hackathon‑Ready Multi‑Agent System (smolagents + Gemini, ReAct)

You are to generate a small, hackathon-ready **Python** project that implements a **three-agent** multi-agent system using **smolagents** with **Gemini (`gemini-2.5-flash`)** as the LLM. The system must support **parallel work** and explicit **handoff** between agents, and follow the **ReAct (Reasoning + Action)** pattern. The primary mission is defined in a file named **`usecase.md`** (assumed to exist in the working directory).

> ⚠️ **Security & privacy**
>
> * **Never print, log, or hardcode secrets.** Read `GEMINI_API_KEY` from environment variables.
> * Do not echo user-provided API keys anywhere in code or docs.

---

## ✅ Deliverables — return all files in one message

**Return exactly these files** (each as its own code block, one block per file, prefixed by a path header). Keep the code compact and readable.

1. **`README.md`** — one-screen quickstart:

   * Install steps.
   * How to set `GEMINI_API_KEY` (e.g., `.env` or shell export).
   * How to run a demo end-to-end.
   * Note: Spanish Gemini quickstart link for reference only (do not paste key).
   * Summarize agents and their roles.

2. **`requirements.txt`**

   * Only: `smolagents`, `google-generativeai`.
   * Use only Python standard library beyond these (e.g., `asyncio`, `concurrent.futures`, `urllib`, `html.parser`, `json`, `pathlib`, `logging`, `time`, `re`).

3. **Package: `multiagents/`**

   * `__init__.py`: empty or simple metadata.
   * `llm_client.py`:

     * Minimal wrapper around `google-generativeai` chat API.
     * Configurable: `model="gemini-2.5-flash"`, `temperature=0.2`, `max_output_tokens=2048`.
     * Function: `generate(messages: list[dict], temperature: float = 0.2) -> str`.
     * Read `GEMINI_API_KEY` from env; basic retry/backoff for 429/5xx.
     * Small helper: `safe_json(obj)` for logging small snippets (no secrets).
   * `mcp_tools.py` (lightweight MCP-style adapter for hackathon speed):

     * Define a tiny `Tool` protocol (`name`, `desc`, `schema`, `run(**kwargs)`).
     * Implement tools (standard library only):

       * `read_file(path: str) -> str`
       * `write_file(path: str, content: str) -> str` (create parents if needed)
       * `http_get(url: str, timeout_sec: int = 10) -> dict` (status, headers, text) using `urllib.request`
       * `web_search(query: str, max_results: int = 5) -> list[dict]` (perform a GET to DuckDuckGo HTML endpoint using `urllib`, parse top links with `html.parser`; return `{title, url}`; be resilient to missing selectors)
     * Include a short note in comments: how to swap to a real MCP server later (map MCP tool JSON-RPC calls to this adapter).
   * `prompts.py` — **working ReAct prompts** (concise, copy-paste runnable):

     * Three prompt strings: `PLANNER_PROMPT`, `RESEARCHER_PROMPT`, `BUILDER_PROMPT`.
     * Each must:

       * Treat `usecase.md` as source of truth.
       * Encourage tool use.
       * Keep chain-of-thought private; only emit short rationales plus actions/observations.
       * Provide **Done** criteria and output contracts.
     * **Visible protocol inside prompts:**

       ```
       You may think silently.
       When acting, use this protocol:
       Action: <tool_name>
       Action Input: <JSON arguments>
       Observation: <tool result summary>
       Final: <final output or status token>
       ```
     * **Roles & contracts:**

       * **Planner** → produce `plan.md` with sections: Objectives, Assumptions, Milestones, Artifacts, Risks & Mitigations, Acceptance Criteria. End with `Final: PLAN_READY`.
       * **Researcher** → from `plan.md` topics, create focused notes: `research/<topic>.md` with brief bullets and source URLs. Emit `Final: RESEARCH_READY:<topic>` per topic.
       * **Builder** → scaffold minimal runnable outputs in `out/` per the plan. Iteratively update when research events appear. End with `Final: BUILD_READY`.
   * `agents.py`

     * Define three smolagents agents wired to `llm_client` and `mcp_tools`:

       * `PlannerAgent`
       * `ResearchAgent`
       * `BuilderAgent`
     * Register tools with each agent:

       * Planner: `read_file`, `write_file` (optional), `web_search` (optional).
       * Researcher: `web_search`, `http_get`, `write_file`.
       * Builder: `read_file`, `write_file`.
     * Implement lean ReAct loops compatible with smolagents’ tool-calling style.
     * Keep logging concise: `[LEVEL] [agent] action=<tool> latency=<ms> note=<short>`.
   * `memory.py`

     * Simple shared KV store and event bus (in-proc):

       * `put(key, value)`, `get(key)`, `subscribe(prefix) -> iterator/async gen`.
       * Used for **handoff** signals like `research:topic_name`.
   * `orchestrator.py`

     * Orchestration with `asyncio`:

       1. Load `usecase.md`; fail fast with friendly message if missing.
       2. Run **Planner** to produce `plan.md`.
       3. Launch **Researcher** and **Builder** **in parallel** using `asyncio.gather`.
       4. **Handoff policy**: Researcher publishes `research:<topic>` events when a note is saved; Builder subscribes and updates outputs.
       5. Stop conditions: (a) Builder reaches `BUILD_READY`, or (b) max steps/time, or (c) both Researcher and Builder idle.
       6. Persist artifacts and print a short final summary.
   * `demo.py` (CLI):

     * `python demo.py --max-steps 12` runs the full loop deterministically (low temperature).
     * Options: `--model`, `--temperature`, `--timeout-sec`.
     * Outputs should include: `plan.md`, at least one `research/*.md`, and at least one file in `out/`.

4. **Top-level `usecase.md`** is assumed to be present. Code should:

   * Read it; if missing, exit with a clear message (no interactive prompts).

---

## 🔧 Implementation & Style Constraints

* Keep it **small, dependency-light, and easy to read**; prefer standard library utilities.
* **ReAct traces**: allow internal reasoning but **do not** print chain-of-thought; surface only:

  * brief rationale (≤1–2 lines),
  * `Action/Action Input/Observation`,
  * `Final: <TOKEN>`.
* Resilience: minimal retries for LLM and network tools; safe file writes (create dirs).
* Determinism: default `temperature=0.2`, cap steps; accept overrides via CLI flags.
* Logging: human-friendly and short.

---

## ✅ Acceptance Criteria (must pass)

* Running `python demo.py` (with `GEMINI_API_KEY` set) produces:

  * `plan.md` with all required sections,
  * `research/` folder with ≥1 topic note including source URLs,
  * `out/` folder with ≥1 artifact aligned to `plan.md`,
  * visible parallelism in logs (Researcher and Builder active together),
  * clear handoff events from Researcher to Builder.
* No secrets printed. No extra dependencies beyond `requirements.txt`.

---

## 📄 File Output Format (strict)

For each file, start with a line like:

```
# FILE: <relative/path>
```

Then add a fenced code block with the file’s contents.

**Example:**

````
# FILE: README.md
```md
...content...
````

````

---

## 🧠 Gemini usage note
Use `google-generativeai` as in the official quickstart (Spanish):

- https://ai.google.dev/gemini-api/docs/quickstart?lang=python&hl=es-419

Do **not** paste any API keys in the repo or output. Read from `os.environ["GEMINI_API_KEY"]`.

---

## 📦 Structured JSON prompt (for tooling)

```json
{
  "task": "Generate a minimal multi-agent Python project (hackathon-ready) using smolagents + Gemini with ReAct, three agents, parallelism, and handoff.",
  "language": "python",
  "framework": "smolagents",
  "model": {
    "provider": "google-generativeai",
    "name": "gemini-2.5-flash",
    "temperature_default": 0.2,
    "max_output_tokens": 2048,
    "env_secret": "GEMINI_API_KEY"
  },
  "security": {
    "no_secret_logging": true,
    "read_secret_from_env": true
  },
  "files_to_output": [
    "README.md",
    "requirements.txt",
    "multiagents/__init__.py",
    "multiagents/llm_client.py",
    "multiagents/mcp_tools.py",
    "multiagents/prompts.py",
    "multiagents/agents.py",
    "multiagents/memory.py",
    "multiagents/orchestrator.py",
    "demo.py"
  ],
  "agents": [
    {
      "name": "PlannerAgent",
      "prompt_key": "PLANNER_PROMPT",
      "tools": ["read_file", "write_file", "web_search"],
      "output_contract": "Generate plan.md with sections: Objectives, Assumptions, Milestones, Artifacts, Risks & Mitigations, Acceptance Criteria. Final token: PLAN_READY."
    },
    {
      "name": "ResearchAgent",
      "prompt_key": "RESEARCHER_PROMPT",
      "tools": ["web_search", "http_get", "write_file"],
      "output_contract": "Create research/<topic>.md notes with bullets + URLs. Emit Final: RESEARCH_READY:<topic> per topic."
    },
    {
      "name": "BuilderAgent",
      "prompt_key": "BUILDER_PROMPT",
      "tools": ["read_file", "write_file"],
      "output_contract": "Write minimal runnable artifacts to out/. Update on research events. Final token: BUILD_READY."
    }
  ],
  "react_protocol": {
    "private_reasoning": true,
    "visible_markers": ["Action", "Action Input", "Observation", "Final"],
    "action_input_format": "JSON"
  },
  "orchestration": {
    "runner": "asyncio",
    "sequence": ["planner", "researcher+builder_parallel"],
    "handoff_bus": "memory.KV with event prefix 'research:'",
    "stop_conditions": ["BUILD_READY", "max_steps", "idle"]
  },
  "tools_mcp": {
    "adapter": "lightweight in-process",
    "tools": [
      {"name": "read_file", "desc": "Read text file"},
      {"name": "write_file", "desc": "Write text file; create parents"},
      {"name": "http_get", "desc": "HTTP GET with urllib"},
      {"name": "web_search", "desc": "DuckDuckGo HTML scrape via urllib + html.parser"}
    ],
    "swap_note": "To replace with a real MCP server, map JSON-RPC tool calls to adapter."
  },
  "constraints": {
    "dependencies": ["smolagents", "google-generativeai"],
    "std_lib_only_beyond_reqs": true,
    "deterministic_defaults": true,
    "friendly_failure_if_usecase_missing": true
  },
  "acceptance": {
    "artifacts": ["plan.md", "research/*", "out/*"],
    "parallelism_visible_in_logs": true,
    "handoff_events_logged": true,
    "no_secrets_printed": true
  },
  "run_command_example": "python demo.py --max-steps 12",
  "docs_link_note": "https://ai.google.dev/gemini-api/docs/quickstart?lang=python&hl=es-419"
}
````
