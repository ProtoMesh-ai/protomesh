from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar
from pydantic import BaseModel, Field
import time

T = TypeVar("T")


class Entity(BaseModel):
    """
    Represents a stored entity with versioning for optimistic concurrency control.
    """

    id: str
    data: Dict[str, Any]
    version: int = 0
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


class StateConflictError(Exception):
    """Raised when an update fails due to a version mismatch."""

    pass


class StateStore(ABC):
    """
    Abstract base class for state storage backends.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Entity]:
        """Retrieve an entity by key."""
        pass

    @abstractmethod
    def set(
        self, key: str, data: Dict[str, Any], expected_version: Optional[int] = None
    ) -> Entity:
        """
        Create or update an entity.

        Args:
            key: The unique key for the entity.
            data: The data to store.
            expected_version: If provided, the update will only succeed if the current
                              version matches this value. If None, it overwrites (blind write)
                              or creates if not exists (depending on implementation,
                              but usually we want explicit creation or version check).

        Returns:
            The updated Entity.

        Raises:
            StateConflictError: If expected_version does not match the current version.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete an entity by key."""
        pass


class InMemoryStateStore(StateStore):
    """
    In-memory implementation of StateStore using a dictionary.
    Thread-safe for the MVP scope (GIL protects dict ops, but logic needs care).
    """

    def __init__(self):
        self._store: Dict[str, Entity] = {}

    def get(self, key: str) -> Optional[Entity]:
        entity = self._store.get(key)
        if entity:
            # Return a copy to prevent direct mutation
            return entity.model_copy(deep=True)
        return None

    def set(
        self, key: str, data: Dict[str, Any], expected_version: Optional[int] = None
    ) -> Entity:
        current = self._store.get(key)

        if expected_version is not None:
            if current is None:
                # Expecting a version but it doesn't exist - conflict unless expecting 0 (creation)
                if expected_version != 0:
                    raise StateConflictError(
                        f"Entity {key} does not exist, but expected version {expected_version}"
                    )
            else:
                if current.version != expected_version:
                    raise StateConflictError(
                        f"Version mismatch for {key}: expected {expected_version}, got {current.version}"
                    )

        # Prepare new entity
        new_version = (current.version + 1) if current else 1
        new_entity = Entity(
            id=key,
            data=data,
            version=new_version,
            created_at=current.created_at if current else time.time(),
            updated_at=time.time(),
        )

        self._store[key] = new_entity
        return new_entity

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]
