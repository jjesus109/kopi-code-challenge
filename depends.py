from pydantic_ai import Agent

from adapters import Adapters
from cases import Cases, CasesInterface
from db import async_engine
from drivers import Drivers

agent = Agent("google-gla:gemini-2.5-flash-lite")


def get_cases() -> CasesInterface:
    return Cases(
        adapters=Adapters(drivers=Drivers(async_engine=async_engine, agent=agent))
    )
