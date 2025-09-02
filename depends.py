from adapters import Adapters
from cases import Cases, CasesInterface
from db import async_engine
from drivers import Drivers


def get_cases() -> CasesInterface:
    return Cases(adapters=Adapters(drivers=Drivers(async_engine=async_engine)))
