from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models import MessageModel
from app.proxy.policy import PolicyInterface


class ProxyInterface(ABC):
    @abstractmethod
    async def valid_message(self, message: str) -> bool:
        raise NotImplementedError


@dataclass
class Proxy(ProxyInterface):
    policy: PolicyInterface

    async def valid_message(self, message: str) -> bool:
        """Validate if the message is allowed to be processed.
        If the action is deny, will return false.
        If the action is warn, will return false. And notify to alert service.
        If the action is allow, will return true.
        If the action is obfuscate, will return true. And obfuscate the message.
        """
        policy_action = await self.policy.decide_policy_action(message)
        if policy_action == "deny":
            return False
        elif policy_action == "warn":
            await self.policy.notify_external_service(message)
            return False
        elif policy_action == "allow":
            return True
        else:
            print("Unknown policy action: ", policy_action)
            return False
