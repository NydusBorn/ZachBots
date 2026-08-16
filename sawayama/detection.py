import json
import os

import cv2
import numpy as np

left_edge = 803
top_edge = 648

left_edge_stack = 976
top_edge_stack = 422

left_edge_suits = 573
top_edge_suits = 397

left_edge_space = 800
top_edge_space = 420


region_width = 28
region_height = 28

suit_gap = 240
stack_gap = 37.8
space_between_columns = 173
space_between_rows = 40

match_slack = 10

rows = 15
cols = 7
stack_cols = 24
suit_count = 4

templates = {}

template_dir = "./templates" if os.path.exists("./templates") else "./sawayama/templates/"

for f in os.listdir(template_dir):
    templates[f.replace(".png", "")] = cv2.imread(f"{template_dir}/{f}", cv2.IMREAD_COLOR)


def match_region(sub_img) -> str:
    best_name = "?"
    best_score = -1.0

    for name, timg in templates.items():
        result = cv2.matchTemplate(sub_img, timg, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)

        if score > best_score:
            best_score = score
            best_name = name

    if best_score < 0.8:
        return "?"

    return best_name


def detect_state(img):
    suits: list[str | None] = [
        "" for _ in range(suit_count)
    ]

    stack: list[str] = []

    space: str = ""

    columns: list[list[str]] = [
        [] for _ in range(cols)
    ]

    for coli in range(cols):
        for rowi in range(rows):
            y0 = top_edge + rowi * space_between_rows - match_slack
            y1 = y0 + region_height + (2 * match_slack)
            x0 = left_edge + coli * space_between_columns - match_slack
            x1 = x0 + region_width + (2 * match_slack)
            region = img[y0:y1, x0:x1]
            match = match_region(region)
            if match == "?":
                break
            columns[coli].append(match)

    for coli in range(stack_cols):
        y0 = top_edge_stack - match_slack
        y1 = y0 + region_height + (2 * match_slack)
        x0 = left_edge_stack + int(coli * stack_gap) - match_slack
        x1 = x0 + region_width + (2 * match_slack)
        region = img[y0:y1, x0:x1]
        match = match_region(region)
        if match == "?":
            break
        stack.append(match)

    for rowi in range(suit_count):
        y0 = top_edge_suits + rowi * suit_gap - match_slack
        y1 = y0 + region_height + (2 * match_slack)
        x0 = left_edge_suits - match_slack
        x1 = x0 + region_width + (2 * match_slack)
        region = img[y0:y1, x0:x1]
        match = match_region(region)
        if match != "?":
            suits[rowi] = match

    y0 = top_edge_space - match_slack
    y1 = y0 + region_height + (2 * match_slack)
    x0 = left_edge_space - match_slack
    x1 = x0 + region_width + (2 * match_slack)

    region = img[y0:y1, x0:x1]
    match = match_region(region)
    if match != "?":
        space = match
    else:
        color_seek = (64,64,64)
        color_match = img[int(y0 + (0.5 * region_height)), int(x0 + (0.5 * region_width))]
        diff = np.mean(cv2.absdiff(color_match, color_seek))
        if diff > 40:
            space = "?"

    ret_dict = {
        "space": space,
        "suits": suits,
        "stack": stack,
        "columns": columns
    }
    return ret_dict


def detect_file(fname: str):
    return detect_state(cv2.imread(fname, cv2.IMREAD_COLOR))


if __name__ == "__main__":
    save = False
    compare = True
    total_errors = 0
    for filename in os.listdir("saves"):
        if filename.endswith(".png"):
            state = detect_file(f"saves/{filename}")
            if compare:
                json_name = filename.replace(".png", ".json")
                if not os.path.exists(f"saves/{json_name}"):
                    continue
                json_content = json.load(open(f"saves/{json_name}"))
                if json_content["space"] == "" and state["space"] != "":
                    print(f"in {filename}: unexpected {state["space"]} in space")
                    total_errors += 1
                elif json_content["space"] != state["space"]:
                    print(f"in {filename}: expected {json_content["space"]} in space, received {state["space"]}")
                    total_errors += 1
                for i in range(suit_count):
                    if json_content["suits"][i] == "" and state["suits"][i] != "":
                        print(f"in {filename}: unexpected {state["suits"][i]} in suit {i}")
                        total_errors += 1
                    elif json_content["suits"][i] != state["suits"][i]:
                        print(f"in {filename}: expected {json_content["suits"][i]} in suit {i}, received {state["suits"][i]}")
                        total_errors += 1
                max_stack = max(len(json_content["stack"]), len(state["stack"]))
                for i in range(max_stack):
                    if i >= len(json_content["stack"]):
                        print(f"in {filename}: unexpected {state["stack"][i]} in stack at {i}")
                        total_errors += 1
                    elif i >= len(state["stack"]):
                        print(f"in {filename}: expected {json_content["stack"][i]} in stack at {i}, received None")
                        total_errors += 1
                    elif json_content["stack"][i] != state["stack"][i]:
                        print(f"in {filename}: expected {json_content["stack"][i]} in stack at {i}, received {state["stack"][i]}")
                        total_errors += 1
                for coli in range(cols):
                    max_row = max(len(json_content["columns"][coli]), len(state["columns"][coli]))
                    for rowi in range(max_row):
                        if rowi >= len(json_content["columns"][coli]):
                            print(f"in {filename}: unexpected {state["columns"][coli][rowi]} in {coli} column at row {rowi}")
                            total_errors += 1
                        elif rowi >= len(state["columns"][coli]):
                            print(f"in {filename}: expected {json_content["columns"][coli][rowi]} in {coli} column at row {rowi}, received None")
                            total_errors += 1
                        elif json_content["columns"][coli][rowi] != state["columns"][coli][rowi]:
                            print(f"in {filename}: expected {json_content["columns"][coli][rowi]} in {coli} column at row {rowi}, received {state["columns"][coli][rowi]}")
                            total_errors += 1
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)
    print(f"total errors: {total_errors}")
