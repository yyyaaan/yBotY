# Yan Pan, 2023
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from prompts.CodeAnalyzer import CodeAnalyzer
from prompts.DocumentQA import DocumentQA
from prompts.VectorStorage import VectorStorage


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
router_open = APIRouter()
router_frontend = APIRouter()


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
@router.post(
    "/chat-document",
    tags=["LLM Structured Answer"],
    response_model=DocumentQA.OutputSchema
)
def chat_document(
    request: Request,
    payload: DocumentQA.InputSchema
):
    """
    chat with document. default collection for chat-about-me feature.
    document must be registered to Chroma DB collection. See /list-collections.
    """
    agent = DocumentQA(
        db_name="aboutme" if payload.collection == "default" else payload.collection,  # noqa: E501
        db_type=payload.database,
        model_name=payload.model,
        trace_func=get_trace_callable(request)
    )
    return agent.ask(payload.question)


@router.get(
    path="/list-collections",
    summary="[non-admin ok] List Chroma DB collections",
    tags=["LLM Admin"],
    response_model=dict
)
async def list_vector_db_collections(request: Request):
    """
    List available collection names in the Chroma DB\n
    The return name can be used for documentQA (/chat) parameters.
    """
    return await VectorStorage.list_vector_db_set()


@router.post(
    path="/create-vector-collection",
    summary="[non-admin ok] Create new vector collection",
    tags=["LLM Admin"],
)
def create_collection_from_file(
    request: Request,
    payload: VectorStorage.InputSchema
):
    """
    Create a ChromaDB collection from an uploaded file.\n
    This actions may take a few minutes to complete; please wait patiently.
    """
    create_func = VectorStorage.chroma_create_persistent_collection
    if payload.database.lower() == "elasticsearch":
        create_func = VectorStorage.elasticsearch_create_persistent_index

    try:
        # VectorStorage.chroma_create_persistent_collection(
        create_func(
            source_file=payload.source_file,
            collection_name=payload.collection_name,
            is_web_url=payload.is_web_url,
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": (
        f"{payload.collection_name} "
        f"created from {payload.source_file}"
    )}


@router.post(
    "/code",
    tags=["LLM Structured Answer"],
    response_model=CodeAnalyzer.OutputSchema
)
def analyze_code(
    request: Request,
    payload: CodeAnalyzer.InputSchema
):
    return CodeAnalyzer(
        temperature=payload.temperature,
        model_name=payload.model,
        trace_func=get_trace_callable(request)
    ).analyze(payload.code)


@router.post("/stream/code", tags=["LLM Streaming Response"])
def analyze_code_stream(
    request: Request,
    payload: CodeAnalyzer.InputSchema
):
    agent = CodeAnalyzer(
        streaming=True,
        temperature=payload.temperature,
        model_name=payload.model,
        trace_func=get_trace_callable(request)
    )
    return StreamingResponse(
        agent.analyze_stream(payload.code),
        media_type="text/event-stream",
        headers={'Connection': 'keep-alive', 'Cache-Control': 'no-cache'}
    )


@router_open.post("/stream/chat-about-me", tags=["LLM Streaming Response"])
def chat_about_me_stream(
    request: Request,
    payload: DocumentQA.InputSchema
):
    db_name = "aboutme" if payload.collection == "default" else payload.collection  # noqa: E501
    if not db_name.startswith("about"):
        raise HTTPException(
            status_code=401,
            detail="this endpoint does not allow using the collection"
        )

    agent = DocumentQA(
        db_name=db_name,
        db_type=payload.database,
        temperature=payload.temperature,
        model_name=payload.model,
        streaming=True,
        trace_func=get_trace_callable(request)
    )

    return StreamingResponse(
        agent.ask_stream(payload.question),
        media_type="text/event-stream",
        headers={'Connection': 'keep-alive', 'Cache-Control': 'no-cache'}
    )


@router.post("/stream/chat-document", tags=["LLM Streaming Response"])
def chat_document_stream(
    request: Request,
    payload: DocumentQA.InputSchema
):
    agent = DocumentQA(
        db_name="aboutme" if payload.collection == "default" else payload.collection,  # noqa: E501
        db_type=payload.database,
        temperature=payload.temperature,
        model_name=payload.model,
        streaming=True,
        trace_func=get_trace_callable(request)
    )
    return StreamingResponse(
        agent.ask_stream(payload.question),
        media_type="text/event-stream",
        headers={'Connection': 'keep-alive', 'Cache-Control': 'no-cache'}
    )


# minimal frontend, not used in production

def render_chat_page(request: Request, name: str, **kwargs):
    return templates.TemplateResponse(
        name="bot/code.html" if "code" in name.lower() else "bot/chat.html",
        context={
            "request": request,
            "endpoint": str(request.url_for(name)),
            **kwargs
        },
    )


@router_frontend.get("/chat", tags=["Frontend"])
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


@router_frontend.get("/chat-file", tags=["Frontend"])
def page_chat_file(request: Request):
    meta = {
        "title": "Chat with a File",
        "desc": "\nI am a chatbot that can answer questions about commonly used files.",  # noqa: E501
        "allow_db_selection": 1
    }
    return render_chat_page(request, "chat_document_stream", **meta)


@router_frontend.get("/chat-web", tags=["Frontend"])
def page_chat_web(request: Request):
    meta = {
        "title": "Chat with a Webpage",
        "desc": (
            "\nI am a chatbot that can answer questions about any webpage."
            "\nPlease provide the URL of the webpage."
        ),
        "allow_input_field": 1
    }
    return render_chat_page(request, "chat_document_stream", **meta)


@router_frontend.get("/code", tags=["Frontend"])
def page_code_analysis(request: Request):
    meta = {
        "title": "Code Analysis Bot",
        "desc": "I am a chatbot that can answer questions about code."
    }
    return render_chat_page(request, "analyze_code_stream", **meta)
