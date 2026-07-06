import json
import os

import cv2
import numpy as np

left_edge = 803
top_edge = 648

left_edge_stack = 976
top_edge_stack = 422

left_edge_suits = 565
top_edge_suits = 389

left_edge_space = 800
top_edge_space = 420


region_width = 28
region_height = 28

suit_gap = 240
stack_gap = 37.8
space_between_columns = 173
space_between_rows = 40


rows = 15
cols = 7
stack_cols = 24
suit_count = 4

templates = {}

template_dir = "./templates" if os.path.exists("./templates") else "./sawayama/templates/"

for f in os.listdir(template_dir):
    templates[f.replace(".png", "")] = cv2.threshold(cv2.imread(f"{template_dir}/{f}", cv2.IMREAD_COLOR), 50, 255, cv2.THRESH_BINARY)[1]


def match_region(sub_img) -> str:
    best_name = "?"
    best_score = -1.0

    for name, timg in templates.items():
        result = cv2.matchTemplate(cv2.threshold(sub_img, 50, 255, cv2.THRESH_BINARY)[1], timg, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)

        if score > best_score:
            best_score = score
            best_name = name

    if best_score < -0.5:
        return "?"

    return best_name


def detect_state(img):
    suits: list[str | None] = [
        None for _ in range(suit_count)
    ]
    
    stack: list[str] = []
    
    space: str | None = None
    
    columns: list[list[str]] = [
        [] for _ in range(cols)
    ]
        
    for coli in range(cols):
        for rowi in range(rows):
            y0 = top_edge + rowi * space_between_rows
            y1 = y0 + region_height
            x0 = left_edge + coli * space_between_columns
            x1 = x0 + region_width
            region = img[y0:y1, x0:x1]
            match = match_region(region)
            if match == "?":
                break
            columns[coli].append(match)
    
    for coli in range(stack_cols):
        y0 = top_edge_stack
        y1 = y0 + region_height
        x0 = left_edge_stack + int(coli * stack_gap)
        x1 = x0 + region_width
        region = img[y0:y1, x0:x1]
        match = match_region(region)
        if match == "?":
            break
        stack.append(match)
    
    for rowi in range(suit_count):
        y0 = top_edge_suits + rowi * suit_gap
        y1 = y0 + region_height
        x0 = left_edge_stack
        x1 = x0 + region_width
        region = img[y0:y1, x0:x1]
        match = match_region(region)
        if match != "?":
            suits[rowi] = match

    y0 = top_edge_space
    y1 = y0 + region_height
    x0 = left_edge_space
    x1 = x0 + region_width
    
    region = img[y0:y1, x0:x1]
    match = match_region(region)
    if match != "?":
        space = match
    else:
        color_seek = (64,64,64)
        color_match = img[y0, x0]
        diff = np.mean(cv2.absdiff(color_match, color_seek))
        if diff > 20:
            space = "?"
    
    print("found")
    

def detect_file(fname: str) -> list[list[str]]:
    return detect_state(cv2.imread(fname, cv2.IMREAD_COLOR))


if __name__ == "__main__":
    save = False
    compare = True
    for filename in os.listdir("saves"):
        if filename.endswith(".png"):
            state = detect_file(f"saves/{filename}")
            if compare:
                json_name = filename.replace(".png", ".json")
                if not os.path.exists(f"saves/{json_name}"):
                    continue
                json_content = json.load(open(f"saves/{json_name}"))
                # TODO
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)