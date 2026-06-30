import random
import threading

import keyboard

import proletariat.actions

games = [proletariat.actions.full_loop]

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
    keyboard.add_hotkey("ctrl+;", switch_state)
    keyboard.wait("ctrl+q")
