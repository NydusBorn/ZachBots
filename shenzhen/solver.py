import enum
import heapq
import json
import os
from ctypes import CField
from typing import Any


class Card:
    def __init__(self, suit: str | None = None, rank: int | None = None):
        self.suit = suit
        self.rank = rank

    @staticmethod
    def from_str(s: str) -> Card:
        c = Card()
        c.suit = s[0]
        if len(s) > 1:
            c.rank = int(s[1:])
        return c

    def is_rank(self):
        return self.rank is not None

    def is_suit(self):
        return self.rank is None

    def __str__(self):
        return f"{self.suit}{self.rank if self.rank is not None else ''}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))


class State:
    def __init__(
        self,
        columns: list[list[Card]],
        cells: list[list[Card]],
        flower_cell: bool,
        completed_cells: list[int],
    ):
        self.flower_cell = flower_cell
        self.columns: list[list[Card]] = []
        self.cells: list[list[Card]] = []
        for col in columns:
            self.columns.append(col.copy())
        for cell in cells:
            self.cells.append(cell.copy())
        self.completed_cells = completed_cells.copy()

    @staticmethod
    def from_str(s: dict[str, list[list[str]] | list[str]]):
        columns = []
        lowest_r = 9
        lowest_g = 9
        lowest_b = 9
        has_flower = False
        for col in s:
            columns.append([])
            for cstr in col:
                c = Card.from_str(cstr)
                if c.is_rank() and c.suit == "R" and c.rank < lowest_r:
                    lowest_r = c.rank
                elif c.is_rank() and c.suit == "G" and c.rank < lowest_g:
                    lowest_g = c.rank
                elif c.is_rank() and c.suit == "B" and c.rank < lowest_b:
                    lowest_b = c.rank
                elif c.suit == "F":
                    has_flower = True
                columns[-1].append(c)

        return State(
            columns,
            [[] for _ in range(3)],
            not has_flower,
            [lowest_r - 1, lowest_g - 1, lowest_b - 1],
        )

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        if self.flower_cell != other.flower_cell:
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
        for compi in range(len(self.completed_cells)):
            if self.completed_cells[compi] != other.completed_cells[compi]:
                return False
        return True

    def __hash__(self):
        return hash(
            (
                tuple(tuple(col) for col in self.columns),
                self.flower_cell,
                tuple(tuple(cell) for cell in self.cells),
                tuple(self.completed_cells),
            )
        )

    def is_win(self):
        for col in self.columns:
            if len(col) != 0:
                return False
        if not self.flower_cell:
            return False
        for rank in self.completed_cells:
            if rank != 9:
                return False
        return True

    def win_estimate(self):
        counter = 0
        for compl in self.completed_cells:
            counter += compl
        return counter

    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def converge(self) -> tuple[int, State | None]:
        # 0 means wait (rank card is removed from field)
        # 1 is press red converge
        # 2 is press green converge
        # 3 is press black converge
        # -1 means nothing can be converged
        for coli, col in enumerate(self.columns):
            if len(col) >= 1 and col[-1].is_rank():
                c = col[-1]
                if c.suit == "R" and self.completed_cells[0] == c.rank - 1 and (
                    self.completed_cells[0] <= 1 or
                    (self.completed_cells[0] <= self.completed_cells[1] and self.completed_cells[0] <= self.completed_cells[2])
                ):
                    new_state = State(
                        self.columns, self.cells, self.flower_cell, self.completed_cells
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[0] += 1
                    return 0, new_state
                elif c.suit == "G" and self.completed_cells[1] == c.rank - 1  and (
                    self.completed_cells[1] <= 1 or
                    (self.completed_cells[1] <= self.completed_cells[0] and self.completed_cells[1] <= self.completed_cells[2])
                ):
                    new_state = State(
                        self.columns, self.cells, self.flower_cell, self.completed_cells
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[1] += 1
                    return 0, new_state
                elif c.suit == "B" and self.completed_cells[2] == c.rank - 1 and (
                    self.completed_cells[2] <= 1 or
                    (self.completed_cells[2] <= self.completed_cells[0] and self.completed_cells[2] <= self.completed_cells[1])
                ):
                    new_state = State(
                        self.columns, self.cells, self.flower_cell, self.completed_cells
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[2] += 1
                    return 0, new_state
            if len(col) >= 1 and col[-1].suit == "F":
                new_state = State(self.columns, self.cells, True, self.completed_cells)
                new_state.columns[coli].pop()
                return 0, new_state
        exposed_suites = [0, 0, 0]
        for cell in self.cells:
            if len(cell) == 1 and cell[0].is_suit():
                if cell[-1].suit == "R":
                    exposed_suites[0] += 1
                elif cell[-1].suit == "G":
                    exposed_suites[1] += 1
                elif cell[-1].suit == "B":
                    exposed_suites[2] += 1
        for col in self.columns:
            if len(col) >= 1 and col[-1].is_suit():
                if col[-1].suit == "R":
                    exposed_suites[0] += 1
                elif col[-1].suit == "G":
                    exposed_suites[1] += 1
                elif col[-1].suit == "B":
                    exposed_suites[2] += 1
        has_free_cell = False
        has_r_in_cells = False
        has_g_in_cells = False
        has_b_in_cells = False
        for cell in self.cells:
            if len(cell) == 0:
                has_free_cell = True
            elif cell[-1].is_suit():
                if cell[-1].suit == "R":
                    has_r_in_cells = True
                elif cell[-1].suit == "G":
                    has_g_in_cells = True
                elif cell[-1].suit == "B":
                    has_b_in_cells = True
        if exposed_suites[0] == 4 and (has_free_cell or has_r_in_cells):
            new_state = State(
                self.columns, self.cells, self.flower_cell, self.completed_cells
            )
            for col in new_state.columns:
                if len(col) >= 1 and col[-1].is_suit() and col[-1].suit == "R":
                    col.pop()
            for cell in new_state.cells:
                if len(cell) >= 1 and cell[-1].is_suit() and cell[-1].suit == "R":
                    cell.pop()
            for cell in new_state.cells:
                if len(cell) == 0:
                    cell.append(Card("R"))
                    break
            return 1, new_state
        elif exposed_suites[1] == 4 and (has_free_cell or has_g_in_cells):
            new_state = State(
                self.columns, self.cells, self.flower_cell, self.completed_cells
            )
            for col in new_state.columns:
                if len(col) >= 1 and col[-1].is_suit() and col[-1].suit == "G":
                    col.pop()
            for cell in new_state.cells:
                if len(cell) >= 1 and cell[-1].is_suit() and cell[-1].suit == "G":
                    cell.pop()
            for cell in new_state.cells:
                if len(cell) == 0:
                    cell.append(Card("G"))
                    break
            return 2, new_state
        elif exposed_suites[2] == 4 and (has_free_cell or has_b_in_cells):
            new_state = State(
                self.columns, self.cells, self.flower_cell, self.completed_cells
            )
            for col in new_state.columns:
                if len(col) >= 1 and col[-1].is_suit() and col[-1].suit == "B":
                    col.pop()
            for cell in new_state.cells:
                if len(cell) >= 1 and cell[-1].is_suit() and cell[-1].suit == "B":
                    cell.pop()
            for cell in new_state.cells:
                if len(cell) == 0:
                    cell.append(Card("B"))
                    break
            return 3, new_state
        return -1, None

    def find_movable_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1..-3 is cells
        movable_cards = []
        for i, col in enumerate(self.columns):
            for rowi in reversed(range(len(col))):
                if rowi == len(col) - 1:
                    movable_cards.append((i, rowi))
                    movable_cards.append((i, rowi))
                elif (
                    col[rowi].is_rank()
                    and col[rowi + 1].is_rank()
                    and col[rowi].suit != col[rowi + 1].suit
                    and col[rowi].rank == col[rowi + 1].rank + 1
                ):
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
        # -1..-3 is cells
        move_spaces = []
        if card_pos[0] < 0:
            card = self.cells[-(card_pos[0] + 1)][0]
        else:
            card = self.columns[card_pos[0]][card_pos[1]]
        for i, col in enumerate(self.columns):
            if len(col) == 0 and card_pos[0] >= 0 and card_pos[1] == 0:
                continue
            if len(col) == 0:
                move_spaces.append((i, len(col)))
            elif (
                col[-1].is_rank()
                and card.is_rank()
                and col[-1].suit != card.suit
                and col[-1].rank == card.rank + 1
            ):
                move_spaces.append((i, len(col) - 1))
        for i, col in enumerate(self.cells):
            if len(col) == 4:
                continue
            if len(col) == 0 and card_pos[0] < 0:
                continue
            if len(col) == 0 and card_pos[1] == len(self.columns[card_pos[0]]) - 1:
                move_spaces.append((-(i + 1), len(col)))
        return move_spaces

    def perform_move(self, from_pos: tuple[int, int], to_pos: int) -> State:
        new_state = State(
            self.columns, self.cells, self.flower_cell, self.completed_cells
        )
        if from_pos[0] >= 0:
            cards = new_state.columns[from_pos[0]][from_pos[1] :]
            new_state.columns[from_pos[0]] = new_state.columns[from_pos[0]][
                : from_pos[1]
            ]
        else:
            cards = [new_state.cells[-(from_pos[0] + 1)]][0]
            new_state.cells[-(from_pos[0] + 1)] = []
        if to_pos >= 0:
            new_state.columns[to_pos].extend(cards)
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
            conv, new_state = state.converge()
            if conv != -1:
                visited[new_state] = (
                    state,
                    (-10 - conv, 0, 0, 0),
                )
                heapq.heappush(queue, new_state)
                if new_state.is_win():
                    found = True
                    found_state = new_state
                continue
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
