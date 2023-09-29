from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from .game import game_loop, process_keypress, state, game_running
from .render import render_state, templates, staticfiles



@asynccontextmanager
async def app_lifespan(app: FastAPI):
    main_loop = asyncio.create_task(game_loop())
    yield
    main_loop.cancel()


app = FastAPI(lifespan=app_lifespan)
app.mount("/static", staticfiles, name="static")


@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    return templates.TemplateResponse(
        "index.jinja2", {"request": request, **state}
    )


@app.post("/keypress", response_class=Response)
async def keypress(request: Request):
    key = (await request.form())["last_key"]
    process_keypress(key)
    return Response(status_code=204)


@app.get("/game-sse")
async def get_game_sse(request: Request) -> EventSourceResponse:
    return EventSourceResponse(render_state(request))
