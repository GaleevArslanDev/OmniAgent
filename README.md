# Omni

Omni is a Python-based autonomous Minecraft agent that connects to a Minecraft server, observes both the world and its own runtime state, uses a local LLM for high-level reasoning, and executes actions through a deterministic task and tool layer.

The project currently combines:
- A Mineflayer-backed Minecraft client through a Python-to-Node bridge
- An Ollama-powered reasoning loop
- A deterministic `TaskPlan` / `TaskProgress` layer for supported multi-step goals
- A persistent `WorldState` for observed world objects
- A separate `AgentState` for the agent's own state
- A modular tool registry for movement, rotation, chat, targeting, and digging

## Ecosystem & Companion Apps

- [Minecraft World Model Viewer](https://github.com/GaleevArslanDev/omni-world-state-visualizer) - a dedicated Panda3D desktop companion app used to monitor and visualize live `world_state.json` updates

## How It Works

On each step, the agent execution loop:
1. Observes the environment and the agent's own state.
2. Updates `WorldState`, `AgentState`, and `TaskProgress`.
3. Builds a prompt from the current observation, action history, memory, `WorldState`, `AgentState`, `TaskPlan`, and `TaskProgress`.
4. Receives exactly one JSON tool call from the local LLM.
5. Executes that tool through the registry.
6. Captures a post-action observation and computes `observation_diff`.
7. Updates `WorldState` and `TaskProgress` from the action result and observed delta.
8. Stops when the task becomes terminal, the LLM uses `done`, or the step limit is reached.

The current toolset allows the agent to handle tasks such as:
- Moving forward for a fixed duration
- Changing body orientation
- Locking gaze at nearby blocks or explicit coordinates
- Sending text updates to the in-game chat
- Mining the block currently under the crosshair
- Tracking and recalling object locations for supported multi-step goals
- Verifying target alignment before digging
- Enforcing expected-block digging and deterministic failure on target mismatch
- Reporting observed world changes after successful interaction
- Answering self-state questions from `AgentState`, including health, food, position, held item, selected slot, and inventory summary

## Architecture & Project Structure

```text
.
|-- main.py                     # Agent entry point and execution loop
|-- llm.py                      # Ollama API call wrapper
|-- prompt.py                   # Prompt construction and context engineering
|-- agent_state.py              # Persistent self-state snapshot of the agent
|-- tool_registry.py            # Tool lookup and execution management
|-- tools_loader.py             # Automatic runtime tool discovery
|-- task_plan.py                # Deterministic task plan parsing
|-- task_progress.py            # Deterministic progress tracking layer
|-- world_state.py              # Persistent observed world state memory
|-- clients/
|   `-- minecraft/              # Mineflayer client bridge and capability mixins
`-- tools/
    |-- common/                 # Shared core tools (for example `done`)
    `-- minecraft/              # Minecraft-specific action implementations
```

## Current State

The repository has already reached `v0.7.0`, the self-state milestone:

- `WorldState` stores observed world objects across steps
- `AgentState` stores the agent's own position, rotation, health, food, selected slot, held item, and inventory snapshot
- Minecraft observations now include `inventory` data in addition to `vision`
- Prompt rules explicitly separate:
  - what the agent sees in the world
  - what the agent has or holds
  - what the deterministic task layer says is already done

At the same time, the project is not yet an inventory-control agent, so the next major unfinished direction starts after `v0.7.0`:

- The agent can reason about inventory contents
- The agent does not yet manage inventory actively: no slot switching, item transfer, chest handling, crafting, or equipment flow

## Core Milestones (Version History)

- **`v0.7.0` (Current)**: Introduced the self-state layer through `AgentState`, extended observations with inventory data, and taught the agent to reason about itself separately from the world
- `v0.6.0`: Hardened object interaction with explicit target flow, look-at verification, expected-block digging, deterministic reporting, and stricter controller termination
- `v0.5.0`: Transitioned task logic to a strict algorithmic layer, isolating execution tracking from LLM hallucination
- `v0.4.0`: Introduced the `WorldState` persistence memory layer and offloaded observation-difference tracking away from the LLM context
- `v0.3.0`: Implemented core environment interaction via the digging tool registry
- `v0.2.0`: Added surrounding world perception
- `v0.1.0`: Configured basic locomotion, rotation, and movement
- `v0.0.0`: Initial text-based agent framework

## Requirements

- Python 3.10+
- Node.js
- Active Minecraft Java server
- Locally installed [Ollama](https://ollama.com)
- The model specified in `llm.py`

Note: the repository includes `package.json` / `package-lock.json` for Node dependencies, but still does not include a Python `requirements.txt`.

## Setup

### 1. Install Dependencies

Install the required Python packages and Node dependencies:

```bash
pip install ollama javascript
npm install
```

### 2. Fetch the Local LLM

Ensure your local Ollama instance is active and download the model specified in `llm.py`:

```bash
ollama pull qwen3:8b
```

### 3. Server Configuration

By default, the client in `clients/minecraft/client.py` connects with:
- Host: `localhost`
- Port: `3000`
- Username: `Omni`

The Minecraft protocol version is not hardcoded by default and may be supplied explicitly when needed.

Modify `clients/minecraft/client.py` directly if your server uses different connection parameters.

## Running the Agent

Launch the main loop:

```bash
python main.py
```

Type your goal directly into the console prompt when requested.

Example prompts:
- `Move forward for 3 seconds`
- `Remember the chest, move forward for 2 seconds, and tell me where the chest was`
- `Turn to the oak_log, break it, and say what changed`
- `What do you have in your inventory?`
- `How much health do you have?`

## Current Development Notes

- Language stance: some core prompt rules and planner-related text are written in Russian, while the runtime architecture itself is language-agnostic
- Observation flow: the standalone `observe` tool is currently not used; environment extraction is handled directly by the main loop
- Task planning scope: `TaskPlan` is intentionally narrow and currently recognizes only a small set of known deterministic multi-step patterns, rather than acting as a general planner
- Interaction semantics: `remember_object_location` means "remember the nearest observed object of the requested type", not every object of that type
- Self-state semantics: `AgentState` is the source of truth for questions about the agent itself, including health, food, coordinates, held item, selected slot, and inventory contents
- Step limit: the agent is hardcoded to stop after 20 sequential tool steps to prevent runaway loops

## Limitations & Next Steps

- Missing Python dependency lockfile / `requirements.txt`
- No automated test suite yet
- The deterministic planner currently supports only a restricted set of sequence patterns
- `report_observation_diff` still relies on LLM wording constrained by prompt rules rather than a fully structured reporting tool
- Inventory reasoning exists, but inventory control tools do not yet
- Connection configuration is still hardcoded in source files
