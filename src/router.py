# Yan Pan, 2023
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from glob import glob

from prompts.CodeAnalyzer import CodeAnalyzer
from prompts.DocumentQA import DocumentQA
from botSettings.settings import Settings


templates = Jinja2Templates(
    # require copy ./templates/bot to parent app
    directory="./templates",
    block_start_string='[%',
    block_end_string='%]',
    variable_start_string='[[',
    variable_end_string=']]',
    comment_start_string='{#',
    comment_end_string='#}',
)

# using two routers for possible fine-tuned auth level
router = APIRouter()
router_me = APIRouter()


def get_trace_callable(request: Request):
    """
    try to get tracing functionality from request.state
    the callable is most likely to come from authentication dependency
    """
    trace_func = None
    try:
        trace_func = request.state.trace
    except AttributeError:
        pass
    except Exception as e:
        print(e)
    return trace_func if callable(trace_func) else print


# backends
@router_me.post(
    "/chat-about-me",
    tags=["LLM Structured Answer"],
    response_model=DocumentQA.OutputSchema
)
def chat_about_me(
    request: Request,
    payload: DocumentQA.InputSchema
):
    agent = DocumentQA(
        db_name="about-me" if payload.collection == "default" else payload.collection,  # noqa: E501
        trace_func=get_trace_callable(request)
    )
    return agent.ask(payload.question)


@router.get(
    path="/list-collections",
    tags=["LLM Structured Answer", "LLM Streaming Response", "LLM Admin"],
    response_model=list[str]
)
def list_chroma_collections(request: Request):
    """
    List available collection names in the Chroma DB\n
    The return name can be used for documentQA (/chat) parameters.
    """
    return [x.split("/")[-1] for x in glob(f"{Settings().CHROMA_PATH}/*")]


@router.post(
    "/code",
    tags=["LLM Structured Answer"],
    response_model=CodeAnalyzer.OutputSchema
)
def analyze_code(
    request: Request,
    payload: CodeAnalyzer.InputSchema
):
    request.app.objs.get("CodeAnalyzer", CodeAnalyzer())
    return CodeAnalyzer().analyze(payload.code)


@router.post("/stream/code", tags=["LLM Streaming Response"])
def analyze_code_stream(
    request: Request,
    payload: CodeAnalyzer.InputSchema
):
    agent = CodeAnalyzer(
        streaming=True,
        trace_func=get_trace_callable(request)
    )
    return StreamingResponse(
        agent.analyze_stream(payload.code),
        media_type="text/event-stream",
    )


@router_me.post("/stream/chat-about-me", tags=["LLM Streaming Response"])
def chat_about_me_stream(
    request: Request,
    payload: DocumentQA.InputSchema
):

    agent = DocumentQA(
        db_name="about-me" if payload.collection == "default" else payload.collection,  # noqa: E501
        temperature=payload.temperature,
        streaming=True,
        trace_func=get_trace_callable(request)
    )
    return StreamingResponse(
        agent.ask_stream(payload.question),
        media_type="text/event-stream",
    )


@router.post("/stream/chat-offer", tags=["LLM Streaming Response"])
def chat_offer_stream(
    request: Request,
    payload: DocumentQA.InputSchema
):
    agent = DocumentQA(
        db_name="kastelli" if payload.collection == "default" else payload.collection,  # noqa: E501
        temperature=payload.temperature,
        streaming=True,
        trace_func=get_trace_callable(request)
    )
    return StreamingResponse(
        agent.ask_stream(payload.question),
        media_type="text/event-stream",
    )


# minimal frontend

def render_chat_page(request: Request, name: str, **kwargs):
    return templates.TemplateResponse(
        name="bot/code.html" if "code" in name.lower() else "bot/chat.html",
        context={
            "request": request,
            "endpoint": str(request.url_for(name)),
            "endpoint2": str(request.url_for("list_chroma_collections")),
            **kwargs
        },
    )


@router_me.get("/chat", tags=["Frontend"])
def page_chat_me(request: Request):
    meta = {
        "title": "About Yan Pan",
        "desc": (
            "\nI am a chatbot that can tell about Yan Pan."
            "\nYou may use any preferred language."
            "\nPlease be aware that even though instructed to be precise and "
            "fact-based, language model could provide inaccurate information."
        ),
    }
    return render_chat_page(request, "chat_about_me_stream", **meta)


@router.get("/chat-file", tags=["Frontend"])
def page_chat_file(request: Request):
    meta = {
        "title": "PDF Chat",
        "desc": "\nI am a chatbot that can answer questions about PDFs.",
        "allow_db_selection": 1
    }
    return render_chat_page(request, "chat_offer_stream", **meta)


@router.get("/chat-web", tags=["Frontend"])
def page_chat_web(request: Request):
    meta = {
        "title": "Chat with a Webpage",
        "desc": (
            "\nI am a chatbot that can answer questions about any webpage."
            "\nPlease provide the URL of the webpage."
        ),
    }
    return render_chat_page(request, "chat_offer_stream", **meta)


@router.get("/code", tags=["Frontend"])
def page_code_analysis(request: Request):
    meta = {
        "title": "Code Analysis",
        "desc": "I am a chatbot that can answer questions about code."
    }
    return render_chat_page(request, "analyze_code_stream", **meta)
