import pytest
from protomesh.core.state import InMemoryStateStore, StateConflictError
from protomesh.core.governance import (
    PolicyEngine,
    AllowListPolicy,
    PolicyContext,
    PolicyViolationError,
)
from protomesh.core.mesh import ProtoMesh


def test_state_store_optimistic_locking():
    store = InMemoryStateStore()

    # Create
    entity = store.set("key1", {"val": 1})
    assert entity.version == 1

    # Update with correct version
    updated = store.set("key1", {"val": 2}, expected_version=1)
    assert updated.version == 2

    # Update with wrong version
    with pytest.raises(StateConflictError):
        store.set("key1", {"val": 3}, expected_version=1)


def test_governance_allow_list():
    engine = PolicyEngine()
    policy = AllowListPolicy(name="TestPolicy", allowed_actions=["read"])
    engine.register_policy(policy)

    # Allowed
    context = PolicyContext(agent_id="test", action="read")
    engine.check_all(context)  # Should not raise

    # Denied
    context = PolicyContext(agent_id="test", action="write")
    with pytest.raises(PolicyViolationError):
        engine.check_all(context)


def test_protomesh_integration():
    mesh = ProtoMesh()
    mesh.governance.register_policy(
        AllowListPolicy(name="p", allowed_actions=["write"], allowed_resources=["test"])
    )

    # Write allowed
    mesh.write("test", {"a": 1}, "agent1")

    # Write denied (resource not allowed)
    with pytest.raises(PolicyViolationError):
        mesh.write("other", {"a": 1}, "agent1")
