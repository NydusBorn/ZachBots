import random
import threading

import keyboard

import proletariat.actions
import sigmars.actions
import sawayama.actions
import cribbage.actions
import cluj.actions
import kabufuda.actions
import shenzhen.actions
import fortune.actions

games = [
    sawayama.actions.full_loop,
    sigmars.actions.full_loop,
    proletariat.actions.full_loop,
    cribbage.actions.full_loop,
    cluj.actions.full_loop,
    kabufuda.actions.full_loop,
    shenzhen.actions.full_loop,
    fortune.actions.full_loop,
]
games_inners = [
    sawayama.actions.loop,
    sigmars.actions.loop,
    proletariat.actions.loop,
    cribbage.actions.loop,
    cluj.actions.loop,
    kabufuda.actions.loop,
    shenzhen.actions.loop,
    fortune.actions.loop,
]

running = threading.Event()

def switch_state():
    if running.is_set():
        running.clear()
    else:
        running.set()
        threading.Thread(target=loop, daemon=True).start()


def loop():
    while running.is_set():
        random.choice(games)()

if __name__ == "__main__":
    keyboard.add_hotkey(";", switch_state)
    for i in range(len(games)):
        keyboard.add_hotkey(str(i + 1), games_inners[i])
    keyboard.wait("ctrl+q")
