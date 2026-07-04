import os
import json
import heapq


class Marble:
    def __init__(self, cls: str | None = None):
        self.cls = cls

    @staticmethod
    def from_str(s: str):
        st = s.replace("Active", "")
        return Marble(st)

    def __str__(self):
        return str(self.cls)
    
    def __repr__(self):
        return str(self.cls)

    def __eq__(self, other):
        if not isinstance(other, Marble):
            return False
        return self.cls == other.cls

    def __hash__(self):
        return hash(self.cls)


class State:
    def __init__(self, marbles: dict[int, dict[int, Marble]]):
        self.marbles: dict[int, dict[int, Marble]] = {}
        self.has_lead = False
        self.has_tin = False
        self.has_iron = False
        self.has_copper = False
        self.has_silver = False
        for k1, v1 in marbles.items():
            ds = {}
            for k2, v2 in v1.items():
                ds[k2] = v2
                if v2.cls == "Lead":
                    self.has_lead = True
                elif v2.cls == "Tin":
                    self.has_tin = True
                elif v2.cls == "Iron":
                    self.has_iron = True
                elif v2.cls == "Copper":
                    self.has_copper = True
                elif v2.cls == "Silver":
                    self.has_silver = True
            self.marbles[k1] = ds

    @staticmethod
    def from_str(s: dict[int, dict[int, str]]):
        marbles: dict[int, dict[int, Marble]] = {}
        for k1, v1 in s.items():
            ds = {}
            for k2, v2 in v1.items():
                ds[int(k2)] = Marble.from_str(v2)
            marbles[int(k1)] = ds
        return State(marbles)

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        for k1, v1 in self.marbles.items():
            for k2, v2 in v1.items():
                if other.marbles.get(k1, None) is None:
                    return False
                if other.marbles[k1].get(k2, None) is None:
                    return False
                if other.marbles[k1][k2] != v2:
                    return False
        return True

    def __hash__(self):
        marble_list = []
        for k1, v1 in self.marbles.items():
            for k2, v2 in v1.items():
                marble_list.append(v2)
        return hash(tuple(marble_list))
    
    def is_win(self):
        for k1, v1 in self.marbles.items():
            if len(v1) != 0:
                return False
        return True
    
    def is_dead_end(self):
        salts = 0
        elements = [0,0,0,0]
        for k1, v1 in self.marbles.items():
            for k2, v2 in v1.items():
                if v2.cls == "Salt":
                    salts += 1
                elif v2.cls == "Fire":
                    elements[0] += 1
                elif v2.cls == "Earth":
                    elements[1] += 1
                elif v2.cls == "Water":
                    elements[2] += 1
                elif v2.cls == "Air":
                    elements[3] += 1
        if salts < sum([elem % 2 == 1 for elem in elements]):
            return True
        return False

    def find_active_positions(self) -> list[tuple[int, int]]:
        # gives row and col of marbles that can be used
        active = []
        for rowi, row in self.marbles.items():
            for coli, marble in row.items():
                neighbors = [
                    self.marbles[rowi].get(coli - 2, None) if self.marbles.get(rowi, None) is not None else None,
                    self.marbles[rowi - 1].get(coli - 1, None) if self.marbles.get(rowi - 1,
                                                                                   None) is not None else None,
                    self.marbles[rowi - 1].get(coli + 1, None) if self.marbles.get(rowi - 1,
                                                                                   None) is not None else None,
                    self.marbles[rowi].get(coli + 2, None) if self.marbles.get(rowi, None) is not None else None,
                    self.marbles[rowi + 1].get(coli + 1, None) if self.marbles.get(rowi + 1,
                                                                                   None) is not None else None,
                    self.marbles[rowi + 1].get(coli - 1, None) if self.marbles.get(rowi + 1,
                                                                                   None) is not None else None,
                ]
                has_contigiuos_space = False
                for i in range(len(neighbors)):
                    if has_contigiuos_space:
                        break
                    contig = 0
                    for j in range(3):
                        pos = (i + j) % len(neighbors)
                        if neighbors[pos] is None:
                            contig += 1
                    if contig == 3:
                        has_contigiuos_space = True
                if has_contigiuos_space:
                    if ((marble.cls == "Tin" and self.has_lead) or
                            (marble.cls == "Iron" and self.has_tin) or
                            (marble.cls == "Copper" and self.has_iron) or
                            (marble.cls == "Silver" and self.has_copper) or
                            (marble.cls == "Gold" and self.has_silver)):
                        continue
                    else:
                        active.append((rowi, coli))
        return active

    def find_possible_actions(self, actionables: list[tuple[int, int]]) -> list[tuple[int, int]]:
        # gives marble ids that can be used (see find_active_positions)
        # either a pair of ids, or the second id of -1 for popping gold
        actions = []
        for i in range(len(actionables)):
            marble1 = self.marbles[actionables[i][0]][actionables[i][1]]
            if (marble1.cls == "Gold"):
                actions.append((i, -1))
                continue
            for j in range(i + 1, len(actionables)):
                marble2 = self.marbles[actionables[j][0]][actionables[j][1]]
                if ((marble1.cls in ["Fire", "Earth", "Water", "Air"] and marble1.cls == marble2.cls) or
                        (marble1.cls in ["Fire", "Earth", "Water", "Air", "Salt"] and marble2.cls == "Salt") or
                        (marble2.cls in ["Fire", "Earth", "Water", "Air", "Salt"] and marble1.cls == "Salt") or
                        (marble1.cls == "Vitae" and marble2.cls == "Mors") or
                        (marble2.cls == "Vitae" and marble1.cls == "Mors") or
                        (marble1.cls in ["Lead", "Tin", "Iron", "Copper", "Silver"] and marble2.cls == "Quicksilver") or
                        (marble2.cls in ["Lead", "Tin", "Iron", "Copper", "Silver"] and marble1.cls == "Quicksilver")):
                    actions.append((i, j))
        return actions

    def perform_action(self, pos1: tuple[int, int], pos2: tuple[int, int] | None):
        new_state = State(self.marbles)
        new_state.marbles[pos1[0]].pop(pos1[1], None)
        if pos2 is not None:
            new_state.marbles[pos2[0]].pop(pos2[1], None)
        return new_state

class Game:
    def __init__(self, state: State):
        self.starter = state

    def DFS(self):
        visited: dict[State, tuple[State, tuple[int, int, int, int]] | None] = {self.starter: None}
        queue: list[State] = [self.starter]

        states_explored = 0
        found = False
        found_state = None
                
        while len(queue) > 0:
            if found:
                break
            state = queue.pop()
            states_explored += 1
            
            actives = state.find_active_positions()
            actions = state.find_possible_actions(actives)
            
            for p1, p2 in actions:
                if found:
                    break
                new_state = state.perform_action(actives[p1], actives[p2] if p2 != -1 else None)
                if new_state not in visited:
                    visited[new_state] = (state, (actives[p1][0], actives[p1][1], actives[p2][0], actives[p2][1]))
                    if new_state.is_dead_end():
                        continue
                    queue.append(new_state)
                    if new_state.is_win():
                        found = True
                        found_state = new_state
            
        path = [visited[found_state]]
        while visited[path[-1][0]] is not None:
            path.append(visited[path[-1][0]])
        return path, states_explored

if __name__ == "__main__":
    for filename in os.listdir("saves"):
        if filename.endswith(".json"):
            json_name = filename.replace(".png", ".json")
            json_content = json.load(open(f"saves/{json_name}"))
            state = State.from_str(json_content)
            game = Game(state)
            print("DFS")
            res = game.DFS()
            print(f"path len = {len(res[0])}")
            print(f"explored = {res[1]}")
