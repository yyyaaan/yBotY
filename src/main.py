# Yan Pan, 2023
# router is used for easy-mount in parent app
import sys
from fastapi import FastAPI, Request

from router import templates, router, router_open, router_frontend
from routerProtected import router_admin_only

# sqlite3 version correction
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

app = FastAPI()


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "bot/index.html", context={"request": request}
    )


app.include_router(router)
app.include_router(router_open)
app.include_router(router_admin_only, prefix="/admin", tags=["LLM Admin"])
# only in this app, if mounted, do not include below
app.include_router(router_frontend)
