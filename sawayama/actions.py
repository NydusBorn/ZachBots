from time import sleep

import keyboard
import pyautogui
import numpy as np
import cv2
from sawayama import detection, solver

enter_game_pos = (155, 1380)

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
    pyautogui.PAUSE = 0.1
    while True:
        pyautogui.moveTo(1000,0)
        screenshot = pyautogui.screenshot()
        state_str = detection.detect_state(cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2RGB))
        starter_state = solver.State.from_str(state_str)
        if starter_state.is_win(): break
        game_solver = solver.Game(starter_state)
        path = game_solver.priority_queue()[0]
        for i, (_, action) in enumerate(path):
            if action[0] == -1:
                pyautogui.moveTo(detection.left_edge_space + hor_offset, detection.top_edge_space)
            elif action[0] == -2:
                pyautogui.moveTo(detection.left_edge_stack + hor_offset + (detection.stack_gap * action[1]), detection.top_edge_stack)
            else:
                pyautogui.moveTo(detection.left_edge + hor_offset + action[0] * detection.space_between_columns, detection.top_edge + ver_offset + action[1] * detection.space_between_rows)
            pyautogui.mouseDown()
            if action[2] == -1:
                pyautogui.moveTo(detection.left_edge_space + hor_offset, detection.top_edge_space)
            else:
                pyautogui.moveTo(detection.left_edge + hor_offset + action[2] * detection.space_between_columns, detection.top_edge + ver_offset + action[3] * detection.space_between_rows)
            pyautogui.mouseUp()
            sleep(0.5)
            scr = pyautogui.screenshot()
            sta_str = detection.detect_state(cv2.cvtColor(np.array(scr), cv2.COLOR_BGR2RGB))
            sta_state = solver.State.from_str(sta_str)
            if i == len(path) - 1:
                break
            if sta_state != path[i + 1][0]:
                while True:
                    sleep(1)
                    pyautogui.moveTo(1000,0)
                    scr = pyautogui.screenshot()
                    n_str = detection.detect_state(cv2.cvtColor(np.array(scr), cv2.COLOR_BGR2RGB))
                    n_state = solver.State.from_str(n_str)
                    if sta_state != n_state:
                        sta_state = n_state
                        continue
                    break
                break
        pyautogui.moveTo(1000,0)
        scr = pyautogui.screenshot()
        n_str = detection.detect_state(cv2.cvtColor(np.array(scr), cv2.COLOR_BGR2RGB))
        n_state = solver.State.from_str(n_str)
        if n_state.space == 0:
            pyautogui.moveTo(detection.left_edge_space + hor_offset, detection.top_edge_space)
            pyautogui.click()
            sleep(2)



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
