import json
import os

import cv2
import numpy as np

left_edge_columns = 495
top_edge_columns = 674

left_edge_cells = 896
top_edge_cells = 320

region_width = 30
region_height = 30

space_between_columns = 204
space_between_rows = 48
space_between_cells = 204

match_slack = 10

rows = 5
cols = 8
cell_count = 4

templates = {}

template_dir = (
    "./templates" if os.path.exists("./templates") else "./kabufuda/templates/"
)

for f in os.listdir(template_dir):
    templates[f.replace(".png", "")] = cv2.imread(
        f"{template_dir}/{f}", cv2.IMREAD_COLOR
    )


def match_region(sub_img) -> str:
    best_name = "?"
    best_score = -1.0

    for name, timg in templates.items():
        result = cv2.matchTemplate(sub_img, timg, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)

        if score > best_score:
            best_score = score
            best_name = name

    if best_score < -0.5:
        return "?"

    return best_name


def detect_state(img):
    columns: list[list[str]] = [[] for _ in range(cols)]
    cells: list[str] = ["" for _ in range(cell_count)]

    for coli in range(cols):
        for rowi in range(rows):
            y0 = top_edge_columns + rowi * space_between_rows - match_slack
            y1 = y0 + region_height + (2 * match_slack)
            x0 = left_edge_columns + coli * space_between_columns - match_slack
            x1 = x0 + region_width + (2 * match_slack)
            region = img[y0:y1, x0:x1]
            match = match_region(region)
            if match == "?":
                break
            columns[coli].append(match)

    for celli in range(cell_count):
        y0 = top_edge_cells
        x0 = left_edge_cells + celli * space_between_cells
        color_seek = (46, 69, 183)
        color_match = img[int(y0 + (0.5 * region_height)), int(x0 + (0.5 * region_width))]
        diff = np.mean(cv2.absdiff(color_match, color_seek))
        if diff > 5:
            cells[celli] = "?"


    ret_dict = {"columns": columns, "cells": cells}

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
                for coli in range(cols):
                    for rowi in range(rows):
                        if (
                            json_content["columns"][coli][rowi]
                            != state["columns"][coli][rowi]
                        ):
                            print(
                                f"in {filename}: expected {json_content['columns'][coli][rowi]} in {coli} column at row {rowi}, received {state['columns'][coli][rowi]}"
                            )
                            total_errors += 1
                for celli in range(cell_count):
                    if (json_content["cells"][celli] != state["cells"][celli]):
                        print(f"in {filename}: expected {json_content['cells'][celli]} in cell {celli}, received {state['cells'][celli]}")
                        total_errors += 1
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)
    print(f"total errors: {total_errors}")
