# Yan Pan, 2023
from fastapi import APIRouter, HTTPException, Request
from json import loads
from uuid import uuid4

from dependencies.docprocessing import DocProcessing
from apis import schemas

router_misc = APIRouter()


@router_misc.get(
    "/list-vector-db",
    tags=["utils"]
)
def list_vector_db(request: Request):
    return request.app.dep.filter_vector_search(
        filter="", distinct=True, remove_scores=True
    )


@router_misc.post("/upload-internal-doc", tags=["utils"])
def upload_doc(request: Request, payload: schemas.FileEmbeddingRequest):
    """
    This endpoint supports txt upload with json metadata
    - tier indicates the quality level of document (0=default)
    """
    try:
        with open(payload.file_path, "r") as f:
            content = f.read()
        texts = content.split("---------\n")
        meta = loads(texts[0])
        res = request.app.dep.embed_and_upload_docs(
            Content=texts[1],
            SourceFileName=payload.file_path.split("/")[-1],
            SourceId=str(uuid4()),
            SourceUrl=meta.get("url", f"local://{payload.file_path}"),
            ChunkTitle=meta.get("title", "no title provided"),
            Category=payload.category,
            TextOffset=0,
            Tier=payload.tier,
            max_tokens=payload.max_tokens,
        )
        return res
    except Exception as e:
        raise HTTPException(500, str(e))


@router_misc.post(
    "/chunk-doc",
    tags=["demo"],
    response_model=schemas.OutputTextChunkRequest,
)
def demo_chunk_doc(request: Request, payload: schemas.FileEmbeddingRequest):
    try:
        with open(payload.file_path, "r") as f:
            text = f.read()
        chunks = DocProcessing.chunk_text_by_sentences(
            text=text,
            max_tokens=payload.max_tokens,
            overlapping_sentences=payload.overlapping_sentences
        )
        n_tokens = [DocProcessing.count_tokens(chunk) for chunk in chunks]
        return {"count": len(chunks), "tokens": n_tokens, "chunks": chunks}
    except Exception as e:
        raise HTTPException(500, str(e))


@router_misc.post("/test", tags=["utils"], deprecated=True)
async def test(
    request: Request, payload: schemas.RouterChainEntry
):
    return {"status": "ok"}
