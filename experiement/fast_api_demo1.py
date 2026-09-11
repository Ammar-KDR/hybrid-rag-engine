from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel, field_validator


class FakeRAGService:
    def __init__(self):
        print("FakeRAGService initialized")

    def ask(self, question: str) -> str:
        return f"Fake answer for: {question}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting application...")

    app.state.rag_service = FakeRAGService()

    yield

    print("Stopping application...")


app = FastAPI(lifespan=lifespan)


class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Question must not be empty.")

        return cleaned


class AskResponse(BaseModel):
    question: str
    answer: str
    abstained: bool


@app.post("/v1/ask", response_model=AskResponse)
def ask(request_body: AskRequest, request: Request):
    rag_service = request.app.state.rag_service

    answer = rag_service.ask(request_body.question)

    return AskResponse(
        question=request_body.question,
        answer=answer,
        abstained=False,
    )