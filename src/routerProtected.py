# Yan Pan, 2023
from fastapi import APIRouter, HTTPException, File, Request, UploadFile
from os import listdir

from botSettings.settings import Settings
from prompts.VectorStorage import VectorStorage
from router import templates

router_admin_only = APIRouter()
file_dir = Settings().UPLOAD_PATH


@router_admin_only.get("/admin")
def admin_panel(request: Request):
    """Admin panel"""
    return templates.TemplateResponse(
        name="bot/admin.html",
        context={"request": request}
    )


@router_admin_only.get("/list-uploaded-files", response_model=list[str])
async def list_uploaded_files(request: Request):
    """List all uploaded files"""
    return [f for f in listdir(file_dir)]


@router_admin_only.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    """Upload file, size is limited by NGINX web server"""
    contents = await file.read()
    try:
        destination = f"{file_dir}/{file.filename}"
        with open(destination, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"filename": destination}


@router_admin_only.post("/create-vector-collection")
def create_collection_from_file(
    request: Request,
    payload: VectorStorage.InputSchema
):
    """
    Create a ChromaDB collection from an uploaded file.\n
    This actions may take a few minutes to complete; please wait patiently.
    """
    if file_dir not in payload.source_file:
        payload.source_file = f"{file_dir}/{payload.source_file}"
    try:
        VectorStorage.chroma_create_persistent_collection(
            source_file=payload.source_file,
            collection_name=payload.collection_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": (
        f"{payload.collection_name} "
        f"created from {payload.source_file}"
    )}


@router_admin_only.post("/delete-vector-collection")
def delete_collection(
    request: Request,
    payload: VectorStorage.InputDelSchema
):
    """Delete a collection from Chroma DB"""
    try:
        VectorStorage.chroma_delete_persistent_collection(
            collection_name=payload.collection_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"{payload.collection_name} deleted"}


@router_admin_only.post("/delete-file")
def delete_file(
    request: Request,
    payload: VectorStorage.InputDelFileSchema
):
    """Delete a collection from Chroma DB"""
    try:
        VectorStorage.delete_filesystem_file(
            filename=payload.filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"{payload.filename} deleted"}
