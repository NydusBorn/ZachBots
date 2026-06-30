import json
import os

import cv2

left_edge = 483
top_edge = 698

region_width = 50
region_height = 30

space_between_columns = 179
space_between_rows = 40

columns = 9
rows = 4

templates = {}

template_dir = "./templates" if os.path.exists("./templates") else "./proletariat/templates/"

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

    return best_name


def detect_state(img) -> list[list[str]]:
    grid = []
    for c in range(columns):
        col = []
        for r in range(rows):
            y0 = top_edge + r * space_between_rows
            y1 = y0 + region_height
            x0 = left_edge + c * space_between_columns
            x1 = x0 + region_width
            region = img[y0:y1, x0:x1]
            col.append(match_region(region))
        grid.append(col)
    return grid


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
                json_content = json.load(open(f"saves/{json_name}"))
                for coli in range(columns):
                    for rowi in range(rows):
                        if json_content[coli][rowi] != state[coli][rowi]:
                            print(f"in {filename}: col {coli}, row {rowi} expected {json_content[coli][rowi]} got {state[coli][rowi]}")
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)
            