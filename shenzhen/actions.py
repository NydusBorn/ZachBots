from time import sleep

import keyboard
import pyautogui
import numpy as np
import cv2
from shenzhen import detection, solver

enter_game_pos = (800, 1380)

top_cells = 260
left_cells = 540

top_buttons = 300
left_buttons = 1175

cells_gap = 200
buttons_gap = 114

def enter_game():
    pyautogui.click(enter_game_pos[0], enter_game_pos[1])
    sleep(0.5)
    keyboard.press_and_release("enter")
    keyboard.press_and_release("enter")
    keyboard.press_and_release("enter")
    keyboard.press_and_release("enter")
    sleep(0.5)

def start_game():
    keyboard.press_and_release("ctrl+n")
    keyboard.press_and_release("ctrl+n")
    keyboard.press_and_release("ctrl+n")
    keyboard.press_and_release("ctrl+n")
    sleep(6)


def exit_game():
    keyboard.press("esc")
    keyboard.press("esc")
    keyboard.press("esc")
    keyboard.press("esc")
    sleep(0.5)

hor_offset = 50
ver_offset = 10

def play_game():
    pyautogui.PAUSE = 0.1
    pyautogui.moveTo(1000,0)
    screenshot = pyautogui.screenshot()
    state_str = detection.detect_state(cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB))
    starter_state = solver.State.from_str(state_str)
    game_solver = solver.Game(starter_state)
    path = game_solver.priority_queue()[0]
    for _, action in path:
        if action[0] <= -10:
            if action[0] == -10:
                sleep(0.5)
            else:
                id = -(action[0] + 10) - 1
                pyautogui.moveTo(left_buttons, top_buttons + id * buttons_gap)
                pyautogui.mouseDown()
                pyautogui.mouseUp()
                sleep(2)
            continue
        elif action[0] < 0:
            pyautogui.moveTo(left_cells + hor_offset + (-(action[0] + 1)) * cells_gap, top_cells + ver_offset)
        else:
            pyautogui.moveTo(detection.left_edge_columns + hor_offset + action[0] * detection.space_between_columns, detection.top_edge_columns + ver_offset + action[1] * detection.space_between_rows)
        pyautogui.mouseDown()
        if action[2] < 0:
            pyautogui.moveTo(left_cells + hor_offset + (-(action[2] + 1)) * cells_gap, top_cells + ver_offset)
        else:
            pyautogui.moveTo(detection.left_edge_columns + hor_offset + action[2] * detection.space_between_columns, detection.top_edge_columns + ver_offset + action[3] * detection.space_between_rows)
        pyautogui.mouseUp()

def loop():
    start_game()
    play_game()

def full_loop():
    enter_game()
    start_game()
    play_game()
    exit_game()

if __name__ == "__main__":
    keyboard.add_hotkey("ctrl+;", loop)
    keyboard.wait("ctrl+q")
