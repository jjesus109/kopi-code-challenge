from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import fastapi
from fastapi import Depends
from fastapi.responses import Response

from cases import CasesInterface
from db import SQLModel, engine
from depends import get_cases
from models import MessageModel, ResponseModel

CasesDeps = Annotated[CasesInterface, Depends(get_cases)]


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI) -> AsyncGenerator[None, None]:
    SQLModel.metadata.create_all(engine)
    yield


app = fastapi.FastAPI(lifespan=lifespan)


@app.post("/chat/", response_model=ResponseModel)
async def send_messages(message: MessageModel, cases: CasesDeps) -> ResponseModel:
    response = await cases.get_response(message)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, port=8080)
