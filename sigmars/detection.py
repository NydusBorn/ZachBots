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
        if name == "ActiveVitae":
            score += 0.25
        elif name == "Vitae":
            score += 0.02

        if score > best_score:
            best_score = score
            best_name = name
    
    if best_score < 0.84:
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
                if not os.path.exists(f"saves/{json_name}"):
                    continue
                json_content = json.load(open(f"saves/{json_name}"))
                for rowi in range(rows):
                    for coli in range(hex_side + min(rowi, rows - 1 - rowi)):
                        col_num = coli * 2 - min(rowi, rows - 1 - rowi)
                        if json_content[str(rowi)].get(str(col_num), None) is None and state[rowi].get(col_num, None) is not None:
                            print(f"in {filename}: unexpected {state[rowi].get(col_num, None)} at row {rowi} col {col_num}")
                        elif json_content[str(rowi)].get(str(col_num), None) != state[rowi].get(col_num, None):
                            print(f"in {filename}: expected {json_content[str(rowi)].get(str(col_num), None)} at row {rowi} col {col_num}, received {state[rowi].get(col_num, None)}")
                        
            if save:
                json_name = filename.replace(".png", ".json")
                with open(f"saves/{json_name}", "w") as f:
                    json.dump(state, f, indent=2)
