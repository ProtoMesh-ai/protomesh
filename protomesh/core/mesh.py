from typing import Any, Dict, Optional
from protomesh.core.state import StateStore, InMemoryStateStore, Entity
from protomesh.core.governance import PolicyEngine, PolicyContext
from protomesh.core.tracing import TraceLogger


class ProtoMesh:
    """
    Main entry point for ProtoMesh middleware.
    Coordinators state, governance, and tracing.
    """

    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        policy_engine: Optional[PolicyEngine] = None,
        logger: Optional[TraceLogger] = None,
    ):
        self.state = state_store or InMemoryStateStore()
        self.governance = policy_engine or PolicyEngine()
        self.tracing = logger or TraceLogger()

    def read(self, key: str) -> Optional[Entity]:
        """Read state for a key."""
        return self.state.get(key)

    def write(
        self,
        key: str,
        data: Dict[str, Any],
        agent_id: str,
        expected_version: Optional[int] = None,
    ) -> Entity:
        """
        Write state with governance checks and tracing.
        """
        # 1. Governance Check
        context = PolicyContext(
            agent_id=agent_id, action="write", resource=key, payload=data
        )
        self.governance.check_all(context)

        # 2. Execute Write
        entity = self.state.set(key, data, expected_version)

        # 3. Trace
        self.tracing.log(
            agent_id=agent_id,
            event_type="state_update",
            payload={"key": key, "version": entity.version},
        )

        return entity

    def check_action(
        self,
        agent_id: str,
        action: str,
        resource: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Explicitly check if an action is allowed."""
        context = PolicyContext(
            agent_id=agent_id, action=action, resource=resource, payload=payload
        )
        self.governance.check_all(context)
