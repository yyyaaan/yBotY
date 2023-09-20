# Yan Pan, 2023
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from chains.RouterChain import RouterChain

from apis import schemas
from templates import TEMPLATES

router_chat = APIRouter()


@router_chat.get('/demo', tags=["demo"])
def demo_page(request: Request):
    return TEMPLATES.TemplateResponse(
        name="chat.html",
        context={"request": request, "desc": """
        This is a demo chat agent implemented with Python and VueJS.
        The demo may contains various bugs from both backend and frontend.
        """}
    )


@router_chat.post("/router-chain", tags=["demo"])
async def router_chain(
    request: Request, payload: schemas.RouterChainEntry
):
    try:
        agent = RouterChain.docs_completion(
            dependencies=request.app.dep,
            available_skills=request.app.skills,
            question=payload.question,
            docIds=payload.docIds,
        )
        return StreamingResponse(agent, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(500, str(e))
