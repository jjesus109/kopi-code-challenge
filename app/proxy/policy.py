import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic_ai import UnexpectedModelBehavior

from app.errors import ModelExecutionError
from app.models import MessageModel
from app.proxy.drivers import ProxyDriversInterface


class PolicyInterface(ABC):
    @abstractmethod
    async def decide_policy_action(self, message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def notify_external_service(self, message: str) -> None:
        raise NotImplementedError


@dataclass
class Policy(PolicyInterface):
    drivers: ProxyDriversInterface

    async def notify_external_service(self, message: str) -> None:
        """Notify an external service with the message."""
        await self.drivers.notify_external_service(message)

    async def decide_policy_action(self, message: str) -> str:
        """
        Decide the policy action for a given message.

        Returns:
            str: One of the following actions:
                - "allow": The request is good and will pass.
                - "deny": The request is not allowed.
                - "warn": Warn about the response by the user or LLM.
                - "obfuscate": Obfuscate PII data.
        """
        # Implement policy logic for prompt injection, PII, abuse, etc

        # Lowercase message for easier matching
        content = message.lower()

        # 1. Prompt Injection/Jailbreak detection
        prompt_injection_patterns = [
            r"ignore\s+all\s+previous\s+instructions",
            r"disregard\s+previous\s+instructions",
            r"pretend\s+to\s+be",
            r"you are now",
            r"as an ai language model",
            r"repeat after me",
            r"system prompt",
            r"reveal your instructions",
            r"forget you are an ai",
            r"bypass",
            r"jailbreak",
            r"write a prompt that",
            r"act as",
            r"simulate",
            r"please provide the system prompt",
            r"what are your instructions",
        ]
        for pattern in prompt_injection_patterns:
            if re.search(pattern, content):
                return "deny"

        # 2. PII detection (very basic, can be improved)
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{16}\b",  # Credit card (very naive)
            r"\b\d{10,11}\b",  # Phone number
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # Email
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP address
        ]
        for pattern in pii_patterns:
            if re.search(pattern, content):
                return "obfuscate"

        # 3. Hate speech, abuse, profanity (very basic, can be improved)
        abuse_patterns = [
            r"\b(fuck|shit|bitch|asshole|bastard|idiot|stupid|dumb|nigger|faggot|cunt|retard|whore|slut)\b",
            r"\b(kill|suicide|die)\b",
            r"\b(hate|abuse|racist|sexist)\b",
        ]
        for pattern in abuse_patterns:
            if re.search(pattern, content):
                return "deny"

        # 4. SQL Injection/XSS/Code Injection
        code_injection_patterns = [
            r"(<script>|</script>)",
            r"(select\s+\*\s+from|drop\s+table|insert\s+into|delete\s+from|update\s+\w+\s+set)",
            r"(;--|--\s|/\*|\*/|@@|@|char\(|nchar\(|varchar\(|alter\s+table|create\s+table)",
            r"(os\.system|subprocess|eval\(|exec\()",
        ]
        for pattern in code_injection_patterns:
            if re.search(pattern, content):
                return "deny"

        # 5. Warn for suspicious but not strictly forbidden content
        warn_patterns = [
            r"\b(secret|password|confidential|private)\b",
            r"\b(hack|exploit|vulnerability)\b",
        ]
        for pattern in warn_patterns:
            if re.search(pattern, content):
                return "warn"

        # If none of the above, allow
        try:
            agent_response = await self.drivers.get_response_from_agent(content)
        except UnexpectedModelBehavior as e:
            raise ModelExecutionError from e
        response: str = agent_response.output.lower()
        return response
