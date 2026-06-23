from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def render_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


def render_crypto_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="crypto.html",
        context={},
    )
