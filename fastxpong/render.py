import asyncio
from os import path
from datetime import datetime
from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates

from .game import state, game_running, bat_moved, ball_moved, scoreboard_changed


base_dir = path.dirname(__file__)
templates = Jinja2Templates(directory=f"{base_dir}/templates")
staticfiles = StaticFiles(directory=f"{base_dir}/static")


async def get_bat(player: str):
    context = {"player": player, "pos": state[player]["pos"]}
    return {
        "event": f"bat_{player}",
        "data": (
            templates.get_template("bat.jinja2").render(context)
        )
    }


async def get_scoreboard():
    return {
        "event": "scoreboard",
        "data": (
            templates.get_template("score.jinja2").render(
                game_running=game_running.is_set(),
                timestamp=datetime.now().isoformat(),
                **state
            )
        )
    }


async def get_ball():
    return {
        "event": "ball",
        "data": (
            templates.get_template("ball.jinja2").render(state)
        )
    }


async def procucer(q, event, getter, args):
    while True:
        await event.wait()
        await q.put(await getter(*args))


async def render_state(request):
    q = asyncio.Queue(2)
    producers = [
        asyncio.create_task(procucer(q, event, getter, args)) for event, getter, args in [
            (ball_moved, get_ball, ()),
            (bat_moved["left"], get_bat, ("left",)),
            (bat_moved["right"], get_bat, ("right",)),
            (scoreboard_changed, get_scoreboard, ()),
        ]
    ]
    try:
        while not await request.is_disconnected():
            item = await q.get()
            try:
                yield item
            finally:
                q.task_done()
    finally:
        for task in producers:
            task.cancel()
