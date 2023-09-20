# Yan Pan, 2023
# %% router is used for easy-mount in parent app
from fastapi import FastAPI, Request
# %%
from dependencies.dependencies import Dependencies
from chains.FunctionCall import FunctionCall
from apis.routerchat import router_chat
from apis.routermisc import router_misc

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """dep injections"""
    app.dep: Dependencies = Dependencies(
        use_gpt4=False,
        use_experimental_search=True,
    )
    app.skills: dict = FunctionCall.collect_available_skills()


@app.get("/", tags=["utils"])
def index(request: Request):
    routes = [{
        "type": type(x).__name__,
        "name": x.name,
        "path": x.path,
    } for x in app.routes]
    routes.sort(key=lambda x: f"{x['type']} {x['path']}")
    return {"info": "hello", "routes": routes}


app.include_router(router_chat)
app.include_router(router_misc)
