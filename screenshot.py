import os

import keyboard
import pyautogui

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")

_next_number = 0


def take_screenshot():
    global _next_number
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"screen_{_next_number}.png"
    _next_number += 1
    filepath = os.path.join(OUTPUT_DIR, filename)
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    print(f"Saved: {filepath}")


if __name__ == "__main__":
    keyboard.add_hotkey("ctrl+;", take_screenshot, suppress=True)
    print("Listening for Ctrl+; ... (press Ctrl+Q to quit)")
    keyboard.wait("ctrl+q")
    print("Exiting.")
