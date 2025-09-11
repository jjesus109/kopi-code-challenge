from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.agent import AgentRunResult


class ProxyDriversInterface(ABC):
    @abstractmethod
    async def get_response_from_agent(self, message: str) -> AgentRunResult:
        raise NotImplementedError

    @abstractmethod
    async def notify_external_service(self, message: str) -> None:
        raise NotImplementedError


@dataclass
class ProxyDrivers(ProxyDriversInterface):
    agent: Agent

    async def get_response_from_agent(self, message: str) -> AgentRunResult:
        return await self.agent.run(message)

    async def notify_external_service(self, message: str) -> None:
        """Notify an external service with the message."""
        # TODO: Implement the external service notification
        # For now, we will mocke this method only printing the message
        print(f"Notifying external service with message: {message}")

    async def obfuscate_message(self, message: str) -> str:
        """Obfuscate the message and returning the obfuscated message."""
        # TODO: Implement the message obfuscation
        # For now, we will mocke this method only printing the message
        print(f"Obfuscating message: {message}")
        return "Obfuscated message"
