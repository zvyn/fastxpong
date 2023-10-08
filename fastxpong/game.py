import asyncio

from .types import StateDict

GAME_LOOP_SLEEP_SECONDS = 0.100


ball_moved = asyncio.Event()
scoreboard_changed = asyncio.Event()
bat_moved = {
    "left": asyncio.Event(),
    "right": asyncio.Event(),
}

state: StateDict = {
    "running": asyncio.Event(),
    "left": {
        "score": 0,
        "pos": 50,
        "len": 10,
        "up_key": "w",
        "down_key": "s",
    },
    "right": {
        "score": 0,
        "pos": 50,
        "len": 10,
        "up_key": "o",
        "down_key": "l",
    },
    "ball": {
        "position": (50.0, 50.0),
        "velocity": (1.0, 0.4),
    },
    "session": {
        "count": 0,
    },
}


def trigger(event: asyncio.Event):
    event.set()
    event.clear()


async def game_loop():
    ball = state["ball"]
    while True:
        await state["running"].wait()

        vx = ball["velocity"][0]
        vy = ball["velocity"][1]
        x = ball["position"][0] + vx
        y = ball["position"][1] + vy
        reset = False

        if x <= 1:
            vx *= -1.0
            if (
                state["left"]["pos"] + state["left"]["len"] + 1.5
                >= y
                >= state["left"]["pos"] - 1.5
            ):
                x = 1.0
                state["left"]["score"] += 1
            else:
                state["ball"]["position"] = 0.0, y
                reset = True
                trigger(ball_moved)
            trigger(scoreboard_changed)
        elif x >= 99:
            vx *= -1.0
            if (
                state["right"]["pos"] + state["right"]["len"] + 1.5
                >= y
                >= state["right"]["pos"] - 1.5
            ):
                x = 98.0
                state["right"]["score"] += 1
            else:
                state["ball"]["position"] = 99.0, y
                reset = True
                trigger(ball_moved)
            trigger(scoreboard_changed)

        if reset:
            state["running"].clear()
            await state["running"].wait()
            state["right"]["score"] = 0
            state["left"]["score"] = 0
            state["ball"]["position"] = 50.0, 50.0
            state["ball"]["velocity"] = 1.0, 0.4
            trigger(scoreboard_changed)
        else:
            if y <= 1.0 or y >= 99.0:
                vy *= -1.0
                y = 1.0 + vy if y < 99.0 else 99.0 + vy
                trigger(scoreboard_changed)

            ball["position"] = x, y
            ball["velocity"] = vx * 1.001, vy * 1.0001
            trigger(ball_moved)

            await asyncio.sleep(GAME_LOOP_SLEEP_SECONDS)


def process_keypress(key):
    if key == "p":
        if state["running"].is_set():
            state["running"].clear()
        else:
            state["running"].set()
        trigger(scoreboard_changed)
        return
    elif not state["running"].is_set():
        return
    for player in ["left", "right"]:
        moved = False
        player_state = state[player]
        if key == player_state["up_key"]:
            pos = state[player]["pos"]
            state[player]["pos"] = max(1, pos - 5)
            moved = True
        elif key == player_state["down_key"]:
            pos = state[player]["pos"]
            state[player]["pos"] = min(100 - state[player]["len"], pos + 5)
            moved = True
        if moved:
            trigger(bat_moved[player])
            return


def process_click(x: float, y: float):
    state["running"].set()
    trigger(scoreboard_changed)
    player = "right" if x > 0.5 else "left"
    pos = state[player]["pos"]
    if (y * 100) - (state[player]["len"] / 2) < pos:
        state[player]["pos"] = max(1, pos - 5)
    else:
        state[player]["pos"] = min(100 - state[player]["len"], pos + 5)
    trigger(bat_moved[player])
