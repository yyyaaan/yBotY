# Yan Pan, 2023
from fastapi import APIRouter, HTTPException, File, Request, UploadFile
from os import listdir

from botSettings.settings import Settings
from prompts.VectorStorage import VectorStorage

router_admin_only = APIRouter()
file_dir = Settings().UPLOAD_PATH


@router_admin_only.get("/admin", summary="Check admin privileges")
def admin_panel(request: Request):
    """only for checking admin privileges"""
    return {"admin": "yes"}
    # return templates.TemplateResponse(
    #     name="bot/admin.html",
    #     context={"request": request}
    # )


@router_admin_only.get("/list-uploaded-files", response_model=list[str])
async def list_uploaded_files(request: Request):
    """List all uploaded files"""
    return [f for f in listdir(file_dir)]


@router_admin_only.post("/create-vector-codebase")
async def create_codebase_vector_db(
    request: Request,
    payload: VectorStorage.InputSchema
):
    """
    collection name will be prefixed with codebase- for frontend use
    Chroma is preferred over elasticsearch for code understanding
    source_file will be ignored.
    """
    docs = VectorStorage.create_codebase_db(
        name=f"codebase-{payload.collection_name}",
        database=payload.database,
    )
    return {"loaded": docs}


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
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"filename": destination}


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
        print(e)
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
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": f"{payload.filename} deleted"}


@router_admin_only.get("/log")
def get_log(request: Request, filename=""):
    """
    Archived logs (not available for today's log)
    """
    available_logs = [
        x for x in listdir("/mnt/shared/fluentd")
        if x.endswith(".log")
    ]

    if filename is not None and len(filename):
        selected_log = filename
    else:
        selected_log = sorted(available_logs)[-1]

    with open(f"/mnt/shared/fluentd/{selected_log}", "r") as f:
        log_content = f.read().split("\n")

    return {
        "log": [f">>> {selected_log} <<<"] + log_content,
        "available": available_logs
    }
