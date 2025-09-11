from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import fastapi
import uvicorn
from fastapi import Depends

from app.configuration import Configuration
from app.db import SQLModel, engine
from app.depends import get_cases
from app.messages.cases import CasesInterface
from app.models import MessageModel, ResponseModel
from app.utils import configure_logger

CasesDeps = Annotated[CasesInterface, Depends(get_cases)]
responses = {
    "400": {"description": "Problems with request"},
    "404": {"description": "Conversation not found"},
    "500": {"description": "Problems with other services"},
}


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    SQLModel.metadata.create_all(engine)
    yield


app = fastapi.FastAPI(
    lifespan=lifespan,
    description="Agent to debate with the user",
    version="0.0.1",
    openapi_url="/api/openapi.json",
)


@app.post("/api/chat/", response_model=ResponseModel, responses=responses)
async def send_messages(message: MessageModel, cases: CasesDeps) -> ResponseModel:
    response = await cases.get_response(message)
    return response


if __name__ == "__main__":
    conf = Configuration()
    configure_logger()
    config = uvicorn.Config(app="app.main:app", port=conf.port, host=conf.host)
    server = uvicorn.Server(config)
    server.run()
