# Yan Pan, 2023
# router is used for easy-mount in parent app
from fastapi import FastAPI, Request

from router import templates, router

app = FastAPI()


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "bot/index.html", context={"request": request}
    )


app.include_router(router)
