from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PolicyContext(BaseModel):
    """Context passed to policies for evaluation."""

    agent_id: str
    action: str
    resource: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class PolicyViolationError(Exception):
    """Raised when a policy is violated."""

    pass


class Policy(ABC):
    """Abstract base class for governance policies."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def check(self, context: PolicyContext) -> bool:
        """
        Check if the action is allowed.
        Returns True if allowed, False otherwise.
        """
        pass

    @abstractmethod
    def reason(self) -> str:
        """Return the reason for the last violation."""
        pass


class AllowListPolicy(Policy):
    """Policy that only allows specific actions or resources."""

    def __init__(
        self,
        name: str,
        allowed_actions: List[str] = None,
        allowed_resources: List[str] = None,
    ):
        self._name = name
        self.allowed_actions = set(allowed_actions or [])
        self.allowed_resources = set(allowed_resources or [])
        self._last_reason = ""

    @property
    def name(self) -> str:
        return self._name

    def check(self, context: PolicyContext) -> bool:
        if self.allowed_actions and context.action not in self.allowed_actions:
            self._last_reason = f"Action '{context.action}' is not in the allow-list."
            return False

        if (
            self.allowed_resources
            and context.resource
            and context.resource not in self.allowed_resources
        ):
            self._last_reason = (
                f"Resource '{context.resource}' is not in the allow-list."
            )
            return False

        return True

    def reason(self) -> str:
        return self._last_reason


class PolicyEngine:
    """Engine to register and enforce policies."""

    def __init__(self):
        self.policies: List[Policy] = []

    def register_policy(self, policy: Policy):
        self.policies.append(policy)

    def check_all(self, context: PolicyContext) -> None:
        """
        Run all policies. Raises PolicyViolationError if any policy fails.
        """
        for policy in self.policies:
            if not policy.check(context):
                raise PolicyViolationError(
                    f"Policy '{policy.name}' violated: {policy.reason()}"
                )
