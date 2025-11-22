from typing import Any, Callable, Dict
from protomesh.core.mesh import ProtoMesh


class ProtoMeshNode:
    """
    Wrapper for LangGraph nodes to inject ProtoMesh capabilities.
    """

    def __init__(self, mesh: ProtoMesh, agent_id: str):
        self.mesh = mesh
        self.agent_id = agent_id

    def __call__(self, func: Callable):
        """Decorator to wrap a node function."""

        def wrapper(state: Dict[str, Any]):
            # Trace node entry
            self.mesh.tracing.log(
                agent_id=self.agent_id,
                event_type="node_start",
                payload={"state_keys": list(state.keys())},
            )

            # Execute node
            try:
                result = func(state, self.mesh)
            except Exception as e:
                self.mesh.tracing.log(
                    agent_id=self.agent_id,
                    event_type="node_error",
                    payload={"error": str(e)},
                )
                raise e

            # Trace node exit
            self.mesh.tracing.log(
                agent_id=self.agent_id,
                event_type="node_end",
                payload={
                    "result_keys": list(result.keys())
                    if isinstance(result, dict)
                    else []
                },
            )
            return result

        return wrapper
