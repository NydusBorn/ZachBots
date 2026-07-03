import json
import os

import cv2

left_edge = 1368 - 5
top_edge = 340 - 5

region_width = 80
region_height = 80

rows = 11
hex_side = 6

col_dist = 88
row_dist = 76

templates = {}

template_dir = "./templates" if os.path.exists("./templates") else "./sigmars/templates/"

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
    
    if best_score < 0.9:
        return "?"
    
    return best_name


def detect_state(img) -> dict[tuple[int, int], str]:
    grid_rows = {}
    
    for rowi in range(rows):
        grid_cols = {}
        for coli in range(hex_side + min(rowi, rows - 1 - rowi)):
            y0 = top_edge + rowi * row_dist
            y1 = y0 + region_height
            x0 = left_edge + coli * col_dist - int(0.5 * col_dist * min(rowi, rows - 1 - rowi))
            x1 = x0 + region_width
            region = img[y0:y1, x0:x1]
            match = match_region(region)
            if match != "?":
                grid_cols[coli * 2 - min(rowi, rows - 1 - rowi)] = match
        grid_rows[rowi] = grid_cols
    return grid_rows


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
                # for coli in range(columns):
                #     for rowi in range(rows):
                #         if json_content[coli][rowi] != state[coli][rowi]:
                #             print(
                #                 f"in {filename}: col {coli}, row {rowi} expected {json_content[coli][rowi]} got {state[coli][rowi]}")
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)
