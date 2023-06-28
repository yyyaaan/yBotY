# Yan Pan, 2023
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(
    directory="templates",
    block_start_string='[%',
    block_end_string='%]',
    variable_start_string='[[',
    variable_end_string=']]',
    comment_start_string='{#',
    comment_end_string='#}',
)


@app.get("/",)
async def index(request:Request):
    return templates.TemplateResponse(
        "index.html", context={"request":request}
    )

