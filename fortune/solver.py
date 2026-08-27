import enum
import heapq
import json
import os
from typing import Any

from cribbage.actions import new_game_pos


class Card:
    def __init__(self, suit: str | None = None, rank: int | None = None):
        self.suit = suit
        self.rank = rank

    @staticmethod
    def from_str(s: str) -> Card:
        c = Card()
        c.suit = s[0]
        match s[1:]:
            case "A":
                c.rank = 1
            case "J":
                c.rank = 11
            case "Q":
                c.rank = 12
            case "K":
                c.rank = 13
            case _:
                c.rank = int(s[1:])
        return c

    def __str__(self):
        return f"{self.suit}{self.rank}"

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
        blocker_cell: Card | None,
        completed_cells: list[int],  # Order is YBGR
        arcana_ends: list[int],  # lower end and higher end
    ):
        self.blocker_cell = blocker_cell
        self.columns: list[list[Card]] = []
        self.cells: list[list[Card]] = []
        for col in columns:
            self.columns.append(col.copy())
        self.completed_cells = completed_cells.copy()
        self.arcana_ends = arcana_ends.copy()

    @staticmethod
    def from_str(s: dict[str, list[list[str]] | list[str]]):
        columns = []
        for col in s:
            columns.append([])
            for cstr in col:
                columns[-1].append(Card.from_str(cstr))

        return State(
            columns,
            None,
            [1 for _ in range(4)],
            [-1, 22],
        )

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        if self.blocker_cell != other.blocker_cell:
            return False
        for coli in range(len(self.columns)):
            if len(self.columns[coli]) != len(other.columns[coli]):
                return False
            for rowi in range(len(self.columns[coli])):
                if self.columns[coli][rowi] != other.columns[coli][rowi]:
                    return False
        for compi in range(len(self.completed_cells)):
            if self.completed_cells[compi] != other.completed_cells[compi]:
                return False
        for arci in range(len(self.arcana_ends)):
            if self.arcana_ends[arci] != other.arcana_ends[arci]:
                return False
        return True

    def __hash__(self):
        return hash(
            (
                tuple(tuple(col) for col in self.columns),
                self.blocker_cell,
                tuple(self.completed_cells),
                tuple(self.arcana_ends),
            )
        )

    def is_win(self):
        for col in self.columns:
            if len(col) != 0:
                return False
        if self.blocker_cell is not None:
            return False
        for rank in self.completed_cells:
            if rank != 13:
                return False
        if self.arcana_ends[0] != self.arcana_ends[1]:
            return False
        return True

    def win_estimate(self):
        counter = 0
        for compl in self.completed_cells:
            counter += compl
        counter += self.arcana_ends[0]
        counter += 22 - self.arcana_ends[1]
        return counter

    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def converge(self) -> tuple[int, State | None]:
        # 0 means wait (card is removed from field)
        # -1 means nothing can be converged
        for coli, col in enumerate(self.columns):
            if len(col) >= 1:
                c = col[-1]
                if (
                    self.blocker_cell is None
                    and c.suit == "Y"
                    and self.completed_cells[0] == c.rank - 1
                ):
                    new_state = State(
                        self.columns,
                        self.blocker_cell,
                        self.completed_cells,
                        self.arcana_ends,
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[0] += 1
                    return 0, new_state
                elif (
                    self.blocker_cell is None
                    and c.suit == "B"
                    and self.completed_cells[1] == c.rank - 1
                ):
                    new_state = State(
                        self.columns,
                        self.blocker_cell,
                        self.completed_cells,
                        self.arcana_ends,
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[1] += 1
                    return 0, new_state
                elif (
                    self.blocker_cell is None
                    and c.suit == "G"
                    and self.completed_cells[2] == c.rank - 1
                ):
                    new_state = State(
                        self.columns,
                        self.blocker_cell,
                        self.completed_cells,
                        self.arcana_ends,
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[2] += 1
                    return 0, new_state
                elif (
                    self.blocker_cell is None
                    and c.suit == "R"
                    and self.completed_cells[3] == c.rank - 1
                ):
                    new_state = State(
                        self.columns,
                        self.blocker_cell,
                        self.completed_cells,
                        self.arcana_ends,
                    )
                    new_state.columns[coli].pop()
                    new_state.completed_cells[3] += 1
                    return 0, new_state
                elif c.suit == "A" and (
                    self.arcana_ends[0] + 1 == c.rank
                    or self.arcana_ends[1] - 1 == c.rank
                ):
                    new_state = State(
                        self.columns,
                        self.blocker_cell,
                        self.completed_cells,
                        self.arcana_ends,
                    )
                    new_state.columns[coli].pop()
                    if self.arcana_ends[0] + 1 == c.rank:
                        new_state.arcana_ends[0] += 1
                    if self.arcana_ends[1] - 1 == c.rank:
                        new_state.arcana_ends[1] -= 1
                    return 0, new_state
        return -1, None

    def find_movable_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1 is blocker cell
        movable_cards = []
        if self.blocker_cell is not None:
            movable_cards.append((-1, 0))
        for i, col in enumerate(self.columns):
            if len(col) != 0:
                movable_cards.append((i, len(col) - 1))
        return movable_cards

    def find_move_spaces(self, card_pos: tuple[int, int]) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1 is blocker cell
        move_spaces = []
        if card_pos[0] < 0:
            card = self.blocker_cell
        else:
            card = self.columns[card_pos[0]][card_pos[1]]
        if card_pos[0] >= 0 and self.blocker_cell is None:
            move_spaces.append((-1, 0))
        for i, col in enumerate(self.columns):
            if len(col) == 0 and card_pos[0] >= 0 and card_pos[1] == 0:
                continue
            if len(col) == 0:
                move_spaces.append((i, len(col)))
            elif col[-1].suit == card.suit and (
                col[-1].rank == card.rank + 1 or col[-1].rank == card.rank - 1
            ):
                move_spaces.append((i, len(col) - 1))
        return move_spaces

    def perform_move(self, from_pos: tuple[int, int], to_pos: int) -> State:
        new_state = State(
            self.columns, self.blocker_cell, self.completed_cells, self.arcana_ends
        )
        if from_pos[0] >= 0:
            card = new_state.columns[from_pos[0]].pop()
        else:
            card = new_state.blocker_cell
            new_state.blocker_cell = None
        if to_pos >= 0:
            new_state.columns[to_pos].append(card)
        else:
            new_state.blocker_cell = card
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
                    (-10, 0, 0, 0),
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
