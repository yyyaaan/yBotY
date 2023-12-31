# Yan Pan, 2023
# router is used for easy-mount in parent app
from fastapi import FastAPI, Request

from router import router, router_open
from routerProtected import router_admin_only

app = FastAPI()


@app.get("/")
def index(request: Request):
    return {"info": "hello world"}


app.include_router(router)
app.include_router(router_open)
app.include_router(router_admin_only, prefix="/admin", tags=["LLM Admin"])
