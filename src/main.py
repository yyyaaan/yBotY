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


# backends

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


@app.post("/stream/chat-offer", tags=["Streaming Response"])
def chat_offer_stream(payload: DocumentQA.InputSchema):
    print(payload)
    return StreamingResponse(
        DocumentQA(
            db_name="kastelli",
            streaming=True
        ).ask_stream(payload.question),
        media_type="text/event-stream",
    )


# minimal frontend

def render_chat_page(request: Request, name: str, **kwargs):
    endpoint = str(request.url_for(name))

    if "localhost" not in endpoint:
        endpoint = endpoint.replace("http://", "https://")

    return templates.TemplateResponse(
        name="chat.html",
        context={"request": request, "endpoint": endpoint, **kwargs},
    )


@app.get("/chat")
def page_chat_me(request: Request):
    desc = """
    I am a chatbot that can tell about Yan Pan.
    You may use any preferred language.
    Please be aware that even though instructed to be precise and fact-based,
    language model can still provide inaccurate information.
    """.replace("  ", "")
    return render_chat_page(
        request, "chat_about_me_stream",
        desc=desc, title="About Yan Pan"
    )


@app.get("/chat1")
def page_chat_one(request: Request):
    meta = {
        "title": "PDF Chat",
        "desc": "\nI am a chatbot that can answer questions about PDFs."
    }
    return render_chat_page(request, "chat_offer_stream", **meta)
