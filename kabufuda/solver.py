import enum
import heapq
import json
import os
from ctypes import CField
from typing import Any


class Card:
    def __init__(self, rank: str | None = None):
        self.suit = rank

    @staticmethod
    def from_str(s: str) -> Card:
        c = Card()
        c.suit = s
        return c

    def __str__(self):
        return str(self.suit)

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit

    def __hash__(self):
        return hash(self.suit)


class State:
    def __init__(
        self,
        columns: list[list[Card]],
        open_cells: int,
        cells: list[list[Card]],
    ):
        self.open_cells = open_cells
        self.columns: list[list[Card]] = []
        self.cells: list[list[Card]] = []
        for col in columns:
            self.columns.append(col.copy())
        for cell in cells:
            self.cells.append(cell.copy())

    @staticmethod
    def from_str(s: dict[str, list[list[str]] | list[str]]):
        columns = []
        for col in s["columns"]:
            columns.append([])
            for cstr in col:
                columns[-1].append(Card.from_str(cstr))
        open_cells = 0
        for cell in s["cells"]:
            open_cells += 1 if cell == "" else 0
        return State(columns, open_cells, [[] for _ in range(4)])

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        if self.open_cells != other.open_cells:
            return False
        for coli in range(len(self.columns)):
            if len(self.columns[coli]) != len(other.columns[coli]):
                return False
            for rowi in range(len(self.columns[coli])):
                if self.columns[coli][rowi] != other.columns[coli][rowi]:
                    return False
        for celli in range(len(self.cells)):
            if len(self.cells[celli]) != len(other.cells[celli]):
                return False
            for rowi in range(len(self.cells[celli])):
                if self.cells[celli][rowi] != other.cells[celli][rowi]:
                    return False
        return True

    def __hash__(self):
        return hash((tuple(tuple(col) for col in self.columns), self.open_cells, tuple(tuple(cell) for cell in self.cells)))

    def is_win(self):
        for col in self.columns:
            if len(col) not in [0, 4]:
                return False
            if len(col) == 4 and any(col[0].suit != card.suit for card in col):
                return False
        for cell in self.cells:
            if len(cell) not in [0, 4]:
                return False
            if len(cell) == 4 and any(cell[0].suit != card.suit for card in cell):
                return False
        return True

    def win_estimate(self):
        counter = 0
        for col in self.columns:
            if len(col) not in [0, 4]:
                counter -= 10
            if len(col) == 4 and any(col[0].suit != card.suit for card in col):
                counter -= 10
        for cell in self.cells:
            if len(cell) not in [0, 4]:
                counter -= 10
            if len(cell) == 4 and any(cell[0].suit != card.suit for card in cell):
                counter -= 10
        return counter

    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def find_movable_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1..-4 is cells
        movable_cards = []
        for i, col in enumerate(self.columns):
            if len(col) == 4 and all(col[0].suit == c.suit for c in col):
                continue
            for rowi in reversed(range(len(col))):
                if rowi == len(col) - 1:
                    movable_cards.append((i, rowi))
                    movable_cards.append((i, rowi))
                elif col[rowi].suit == col[rowi + 1].suit:
                    movable_cards.pop()
                    movable_cards.append((i, rowi))
                else:
                    break
        for i, col in enumerate(self.cells):
            if len(col) == 4:
                continue
            if len(col) == 1:
                movable_cards.append((-(i + 1), 0))
        return movable_cards

    def find_move_spaces(self, card_pos: tuple[int, int]) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1..-4 is cells
        move_spaces = []
        if card_pos[0] < 0:
            card = self.cells[-(card_pos[0] + 1)][0]
        else:
            card = self.columns[card_pos[0]][card_pos[1]]
        for i, col in enumerate(self.columns):
            if len(col) == 4 and all(col[0].suit == c.suit for c in col):
                continue
            if len(col) == 0 and card_pos[0] >= 0 and card_pos[1] == 0:
                continue
            if len(col) == 0:
                move_spaces.append((i, len(col)))
            elif col[-1].suit == card.suit:
                move_spaces.append((i, len(col) - 1))
        for i, col in enumerate(self.cells):
            if i >= self.open_cells:
                continue
            if len(col) == 4 and all(col[0].suit == c.suit for c in col):
                continue
            if len(col) == 0 and card_pos[0] < 0:
                continue
            if len(col) == 0 and card_pos[1] == len(self.columns[card_pos[0]]) - 1:
                move_spaces.append((-(i + 1), len(col)))
            elif card_pos[0] >= 0 and len(col) == 1 and col[-1].suit == card.suit and card_pos[1] == len(self.columns[card_pos[0]]) - 3:
                move_spaces.append((-(i + 1), len(col) - 1))
        return move_spaces

    def perform_move(self, from_pos: tuple[int, int], to_pos: int) -> State:
        new_state = State(self.columns, self.open_cells, self.cells)
        if from_pos[0] >= 0:
            cards = new_state.columns[from_pos[0]][from_pos[1] :]
            new_state.columns[from_pos[0]] = new_state.columns[from_pos[0]][: from_pos[1]]
        else:
            cards = [new_state.cells[-(from_pos[0] + 1)]][0]
            new_state.cells[-(from_pos[0] + 1)] = []
        if to_pos >= 0:
            new_state.columns[to_pos].extend(cards)
            if len(new_state.columns[to_pos]) == 4 and all(new_state.columns[to_pos][0].suit == c.suit for c in new_state.columns[to_pos]):
                new_state.open_cells += 1
        else:
            new_state.cells[-(to_pos + 1)].extend(cards)
        return new_state


class Game:
    def __init__(self, state: State):
        self.starter = state

    def priority_queue(self):
        # visited is a map from target state to source state and the action required to get from source to target in format from col from row to col to row
        visited: dict[State, tuple[State, tuple[int, int, int, int]] | None] = {
            self.starter: None
        }
        queue: list[State] = [self.starter]

        states_explored = 0
        found = False
        found_state = None

        while len(queue) > 0:
            if found:
                break
            state = heapq.heappop(queue)
            states_explored += 1
            for movable in state.find_movable_cards():
                if found:
                    break
                for moveto in state.find_move_spaces(movable):
                    if found:
                        break
                    new_state = state.perform_move(movable, moveto[0])
                    if new_state not in visited:
                        visited[new_state] = (
                            state,
                            (movable[0], movable[1], moveto[0], moveto[1]),
                        )
                        heapq.heappush(queue, new_state)
                        if new_state.is_win():
                            found = True
                            found_state = new_state
        path = [visited[found_state]]
        while visited[path[-1][0]] is not None:
            path.append(visited[path[-1][0]])
        path.reverse()
        return path, states_explored


if __name__ == "__main__":
    for filename in os.listdir("saves"):
        if filename.endswith(".json"):
            json_name = filename.replace(".png", ".json")
            json_content = json.load(open(f"saves/{json_name}"))
            state = State.from_str(json_content)
            game = Game(state)
            print("Priority Queue")
            res = game.priority_queue()
            print(f"path len = {len(res[0])}")
            print(f"explored = {res[1]}")
