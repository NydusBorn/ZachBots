import json
import os

import cv2
import numpy as np

left_edge_columns = 537 + 10
top_edge_columns = 612 + 15

region_width = 30
region_height = 30

space_between_columns = 203
space_between_rows = 41

match_slack = 10

rows = 5
cols = 8

templates = {}

template_dir = (
    "./templates" if os.path.exists("./templates") else "./shenzhen/templates/"
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

    red = (174, 44, 20) # RGB
    red = (20, 44, 174) # BGR
    green = (18, 110, 75) # RGB
    green = (75, 110, 18) # BGR
    black = (0, 0, 0)

    if best_score < 0.6:
        return "?"

    if best_name.isdigit():
        shp = sub_img.shape
        for i in range(shp[0]):
            for j in range(shp[1]):
                if all(sub_img[i, j, k] == red[k] for k in range(3)):
                    best_name = f"R{best_name}"
                    return best_name
                elif all(sub_img[i, j, k] == green[k] for k in range(3)):
                    best_name = f"G{best_name}"
                    return best_name
                elif all(sub_img[i, j, k] == black[k] for k in range(3)):
                    best_name = f"B{best_name}"
                    return best_name

    return best_name


def detect_state(img):
    columns: list[list[str]] = [[] for _ in range(cols)]

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

    return columns


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
                    max_row = max(len(json_content[coli]), len(state[coli]))
                    for rowi in range(max_row):
                        if rowi >= len(json_content[coli]):
                            print(
                                f"in {filename}: unexpected {state[coli][rowi]} in {coli} column at row {rowi}"
                            )
                            total_errors += 1
                        elif rowi >= len(state[coli]):
                            print(
                                f"in {filename}: expected {json_content[coli][rowi]} in {coli} column at row {rowi}, received None"
                            )
                            total_errors += 1
                        elif json_content[coli][rowi] != state[coli][rowi]:
                            print(
                                f"in {filename}: expected {json_content[coli][rowi]} in {coli} column at row {rowi}, received {state[coli][rowi]}"
                            )
                            total_errors += 1
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)
    print(f"total errors: {total_errors}")
