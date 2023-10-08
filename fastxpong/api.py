from contextlib import asynccontextmanager
import asyncio
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from .game import (
    game_loop,
    process_click,
    process_keypress,
    state,
    scoreboard_changed,
    trigger,
)
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
    return EventSourceResponse(session_counter(render_state(request)))
