import asyncio
from datetime import datetime
from typing import Literal

from .game import state, bat_moved, ball_moved, scoreboard_changed
from .api import templates


async def get_bat(player: Literal["left", "right"]):
    context = {"player": player, "pos": state[player]["pos"]}
    return {
        "event": f"bat_{player}",
        "data": await templates.get_template("bat.jinja2").render_async(context),
    }


async def get_scoreboard():
    return {
        "event": "scoreboard",
        "data": (
            await templates.get_template("score.jinja2").render_async(
                timestamp=datetime.now().isoformat(),
                **state,
            )
        ),
    }


async def get_ball():
    return {
        "event": "ball",
        "data": (await templates.get_template("ball.jinja2").render_async(state)),
    }


async def producer(q, event, getter, args):
    await q.put(await getter(*args))
    while True:
        await event.wait()
        await q.put(await getter(*args))


async def render_state(request):
    q = asyncio.Queue(4)
    producers = [
        asyncio.create_task(producer(q, event, getter, args))
        for event, getter, args in [
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
