# Yan Pan, 2023
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from prompts.CodeAnalyzer import CodeAnalyzer


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


@app.post("/code", response_model=CodeAnalyzer.OutputSchema)
def analyze_code(request: Request, payload: CodeAnalyzer.InputSchema):
    return CodeAnalyzer().analyze(payload.code)


@app.post("/code/stream", )
def analyze_code_stream(payload: CodeAnalyzer.InputSchema):
    return StreamingResponse(
        CodeAnalyzer(streaming=True).analyze_stream(payload.code),
        media_type="text/event-stream",
    )
