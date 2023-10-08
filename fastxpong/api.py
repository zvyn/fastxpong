from os import path
from contextlib import asynccontextmanager
import asyncio
from typing import cast
from logging import getLogger

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

from .game import (
    game_loop,
    process_click,
    process_keypress,
    state,
    scoreboard_changed,
    trigger,
)

logger = getLogger(__name__)
base_dir = path.dirname(__file__)
templates = Jinja2Templates(directory=f"{base_dir}/templates", enable_async=True)
staticfiles = StaticFiles(directory=f"{base_dir}/static")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    await asyncio.get_running_loop().run_in_executor(None, ensure_htmx)
    main_loop = asyncio.create_task(game_loop())
    yield
    main_loop.cancel()


def ensure_htmx():
    for expected, source in {
        "htmx.min.js": "https://unpkg.com/htmx.org@1.9.6/dist/htmx.min.js",
        "sse.js": "https://unpkg.com/htmx.org@1.9.6/dist/ext/sse.js",
    }.items():
        file_name = f"{staticfiles.directory}/{expected}"
        if not path.exists(file_name):
            logger.warning(
                "Loading %(file_name)s from %(source)s",
                {"file_name": file_name, "source": source},
            )
            resp = requests.get(source)
            resp.raise_for_status()
            with open(file_name, "wb") as f:
                f.write(resp.content)


app = FastAPI(lifespan=app_lifespan)
app.mount("/static", staticfiles, name="static")


@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    return HTMLResponse(
        await templates.get_template("index.jinja2").render_async(
            {"request": request, **state}
        ),
    )


@app.post("/keypress", response_class=Response)
async def keypress(request: Request):
    key = (await request.form()).get("last_key")
    if key:
        process_keypress(key)
    return Response(status_code=204)


@app.post("/click", response_class=Response)
async def click(request: Request):
    form_data = await request.form()
    try:
        x = float(cast(str, form_data["x"]))
        y = float(cast(str, form_data["y"]))
    except (KeyError, ValueError):
        pass
    else:
        process_click(x, y)
    return Response(status_code=204)


async def session_counter(async_generator):
    state["session"]["count"] += 1
    try:
        yield await anext(async_generator)
        async for value in async_generator:
            yield value
    finally:
        state["session"]["count"] -= 1
        trigger(scoreboard_changed)


@app.get("/game-sse")
async def get_game_sse(request: Request) -> EventSourceResponse:
    from .render import render_state

    return EventSourceResponse(session_counter(render_state(request)))
