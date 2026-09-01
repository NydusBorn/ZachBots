from time import sleep

import keyboard
import pyautogui
import numpy as np
import cv2
from kabufuda import detection, solver

enter_game_pos = (1800, 1380)
diff_sel_pos = (1500,1000)

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
    pyautogui.click(diff_sel_pos[0], diff_sel_pos[1])
    pyautogui.click(diff_sel_pos[0], diff_sel_pos[1])
    pyautogui.click(diff_sel_pos[0], diff_sel_pos[1])
    pyautogui.click(diff_sel_pos[0], diff_sel_pos[1])
    sleep(5)


def exit_game():
    keyboard.press("esc")
    keyboard.press("esc")
    keyboard.press("esc")
    keyboard.press("esc")
    sleep(0.5)

hor_offset = 50
ver_offset = 20

def play_game():
    pyautogui.PAUSE = 0.1
    pyautogui.moveTo(1000,0)
    screenshot = pyautogui.screenshot()
    state_str = detection.detect_state(cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB))
    starter_state = solver.State.from_str(state_str)
    game_solver = solver.Game(starter_state)
    path = game_solver.priority_queue()[0]
    for _, action in path:
        if action[0] < 0:
            pyautogui.moveTo(detection.left_edge_cells + hor_offset + (-(action[0] + 1)) * detection.space_between_cells, detection.top_edge_cells + ver_offset)
        else:
            pyautogui.moveTo(detection.left_edge_columns + hor_offset + action[0] * detection.space_between_columns, detection.top_edge_columns + ver_offset + action[1] * detection.space_between_rows)
        pyautogui.mouseDown()
        if action[2] < 0:
            pyautogui.moveTo(detection.left_edge_cells + hor_offset + (-(action[2] + 1)) * detection.space_between_cells, detection.top_edge_cells + ver_offset)
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
