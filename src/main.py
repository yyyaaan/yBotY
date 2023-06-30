# Yan Pan, 2023
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from prompts.CodeAnalyzer import CodeAnalyzer
from prompts.DocumentQA import DocumentQA

app = FastAPI()
templates = Jinja2Templates(
    directory="templates",
    block_start_string='[%',
    block_end_string='%]',
    variable_start_string='[[',
    variable_end_string=']]',
    comment_start_string='{#',
    comment_end_string='#}',
)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", context={"request": request}
    )


@app.post(
    "/code",
    tags=["Structured Answer"],
    response_model=CodeAnalyzer.OutputSchema
)
def analyze_code(payload: CodeAnalyzer.InputSchema):
    return CodeAnalyzer().analyze(payload.code)


@app.post("/stream/code", tags=["Streaming Response"])
def analyze_code_stream(payload: CodeAnalyzer.InputSchema):
    return StreamingResponse(
        CodeAnalyzer(streaming=True).analyze_stream(payload.code),
        media_type="text/event-stream",
    )


@app.post(
    "/chat-about-me",
    tags=["Structured Answer"],
    response_model=DocumentQA.OutputSchema
)
def chat_about_me(payload: DocumentQA.InputSchema):
    return DocumentQA(db_name="yan-tietoevry-doc").ask(payload.question)


@app.post("/stream/chat-about-me", tags=["Streaming Response"])
def chat_about_me_stream(payload: DocumentQA.InputSchema):
    return StreamingResponse(
        DocumentQA(
            db_name="yan-tietoevry-doc",
            streaming=True
        ).ask_stream(payload.question),
        media_type="text/event-stream",
    )
