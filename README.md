# ProtoMesh
> Cross-framework orchestration for AI agents.

ProtoMesh is a middleware for orchestrating multi-agent systems, enabling seamless integration between frameworks like LangGraph and CrewAI with shared state, optimistic locking, and policy-based governance.

## Features
- **Shared State Fabric**: In-memory store with optimistic concurrency control (versioning).
- **Governance Engine**: Pre-execution hooks for policies (e.g., AllowLists).
- **Adapters**: Native integration for LangGraph (Nodes) and CrewAI (Tools).
- **Observability**: JSON-based event tracing.

## Installation

Requires Python 3.12+.

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Usage

### Core Concepts

```python
from protomesh.core.mesh import ProtoMesh
from protomesh.core.governance import AllowListPolicy

# Initialize Mesh
mesh = ProtoMesh()

# Add Governance Policy
policy = AllowListPolicy(name="SecureWrite", allowed_actions=["write"])
mesh.governance.register_policy(policy)

# Write State (with tracing and policy check)
mesh.write("key1", {"status": "active"}, agent_id="agent-007")

# Read State
entity = mesh.read("key1")
print(entity.data)
```

### Running the Demo

A full example integrating CrewAI and LangGraph is available in [`protomesh/examples/demo_workflow.py`](./protomesh/examples/demo_workflow.py).

Requires `GOOGLE_API_KEY` for Gemini/ or you can modify it for other LLMs in [`protomesh/examples/demo_workflow.py`](./protomesh/examples/demo_workflow.py) as it uses [LiteLLM](https://www.litellm.ai/).

```bash
export GOOGLE_API_KEY=your_key_here
python protomesh/examples/demo_workflow.py
```

## Testing

Run unit tests:

```bash
pytest tests/
```