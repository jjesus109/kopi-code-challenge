from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import fastapi
from fastapi import Depends
from fastapi.responses import Response
from pydantic_ai import Agent

from cases import CasesInterface
from db import SQLModel, engine
from depends import get_cases
from models import MessageModel

CasesDeps = Annotated[CasesInterface, Depends(get_cases)]


agent = Agent("google-gla:gemini-2.5-flash")


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    SQLModel.metadata.create_all(engine)
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.post("/chat/")
async def send_messages(message: MessageModel, cases: CasesDeps) -> Response:
    await cases.insert_message(message)
    return Response(status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
