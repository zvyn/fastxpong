import asyncio

from .types import StateDict

GAME_LOOP_SLEEP_SECONDS = .100


game_running = asyncio.Event()
ball_moved = asyncio.Event()
scoreboard_changed = asyncio.Event()
bat_moved = {
    "left": asyncio.Event(),
    "right": asyncio.Event(),
}

state: StateDict = {
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
        "position": (50, 50),
        "velocity": (1, .4),
    },
}


async def reset_score():
    game_running.clear()
    await asyncio.sleep(0)
    state["right"]["score"] = 0
    state["left"]["score"] = 0
    state["ball"]["position"] = 50, 50
    state["ball"]["velocity"] = 1, .4
    await game_running.wait()
    scoreboard_changed.set()
    scoreboard_changed.clear()


async def game_loop():
    ball = state["ball"]
    while True:
        await game_running.wait()

        vx = ball["velocity"][0]
        vy = ball["velocity"][1]
        x = ball["position"][0] + vx
        y = ball["position"][1] + vy
        reset = False

        if x <= 0:
            x = 1
            vx *= -1
            if state["left"]["pos"] + state["left"]["len"] >= y >= state["left"]["pos"]:
                state["left"]["score"] += 1
            else:
                reset = True
            scoreboard_changed.set()
            scoreboard_changed.clear()
        elif x >= 99:
            x = 98
            vx *= -1
            if state["right"]["pos"] + state["right"]["len"] >= y >= state["right"]["pos"]:
                state["right"]["score"] += 1
            else:
                reset = True
            scoreboard_changed.set()
            scoreboard_changed.clear()

        if reset:
            await reset_score()
            continue

        if y <= 0:
            y = 1
            vy *= -1
        if y >= 99:
            y = 98
            vy *= -1

        ball["position"] = x, y
        ball["velocity"] = vx * 1.001, vy * 1.0001
        ball_moved.set()
        ball_moved.clear()

        await asyncio.sleep(GAME_LOOP_SLEEP_SECONDS)


def process_keypress(key):
    if key == "p":
        if game_running.is_set():
            game_running.clear()
        else:
            game_running.set()
        scoreboard_changed.set()
        scoreboard_changed.clear()
        return
    elif not game_running.is_set():
        return
    for player in ["left", "right"]:
        moved = False
        player_state = state[player]
        if key == player_state["up_key"]:
            pos = state[player]["pos"]
            state[player]["pos"] = max(0, pos - 5)
            moved = True
        elif key == player_state["down_key"]:
            pos = state[player]["pos"]
            state[player]["pos"] = min(
                100 - state[player]["len"], pos + 5
            )
            moved = True
        if moved:
            bat_moved[player].set()
            bat_moved[player].clear()
            return