from time import sleep

import keyboard
import pyautogui
import numpy as np
import cv2

from proletariat.detection import region_width
from sigmars import detection, solver

enter_game_pos = (500, 1380)
space_pos = (1900, 480)


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
    pyautogui.PAUSE = 0.2
    pyautogui.moveTo(1000,0)
    screenshot = pyautogui.screenshot()
    state_str = detection.detect_state(cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB))
    starter_state = solver.State.from_str(state_str)
    game_solver = solver.Game(starter_state)
    path = game_solver.DFS()[0]
    for _, action in path:
        rowi_in = action[0]
        coli_in = action[1]
        rowi_out = action[2]
        coli_out = action[3]
        pyautogui.moveTo(detection.left_edge + int(0.5 * detection.region_width) + coli_in * (detection.col_dist // 2),
                        detection.top_edge + int(0.5 * detection.region_height) + rowi_in * detection.row_dist)
        pyautogui.click()
        if rowi_out != -999:
            pyautogui.moveTo(detection.left_edge + int(0.5 * detection.region_width) + coli_out * (detection.col_dist // 2),
                            detection.top_edge + int(0.5 * detection.region_height) + rowi_out * detection.row_dist)
            pyautogui.click()

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
