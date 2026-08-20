import enum
import heapq
import json
import os
from typing import Any


class Card:
    def __init__(self, rank: int | None = None):
        self.rank = rank

    @staticmethod
    def from_str(s: str) -> Card:
        c = Card()
        match s:
            case "T":
                c.rank = 14
            case "K":
                c.rank = 13
            case "D":
                c.rank = 12
            case "V":
                c.rank = 11
            case x:
                c.rank = int(x)
        return c

    def __str__(self):
        return str(self.rank)

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank

    def __hash__(self):
        return hash(self.rank)


class State:
    def __init__(
        self,
        columns: list[list[Card]],
    ):
        self.columns: list[list[Card]] = []
        for col in columns:
            self.columns.append(col.copy())

    @staticmethod
    def from_str(s: list[list[str]]):
        columns = []
        for col in s:
            columns.append([])
            for cstr in col:
                columns[-1].append(Card.from_str(cstr))
        return State(columns)

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        for coli in range(len(self.columns)):
            if len(self.columns[coli]) != len(other.columns[coli]):
                return False
            for rowi in range(len(self.columns[coli])):
                if self.columns[coli][rowi] != other.columns[coli][rowi]:
                    return False
        return True

    def __hash__(self):
        return hash((tuple(tuple(col) for col in self.columns),))

    def is_win(self):
        for col in self.columns:
            if len(col) not in [0, 9]:
                return False
            if len(col) == 9:
                for i, c in enumerate(col):
                    if c.rank != 14 - i:
                        return False
        return True

    def win_estimate(self):
        counter = 0
        for col in self.columns:
            last_card = None
            if len(col) not in [0, 9]:
                counter -= 1
            if len(col) == 9 and all(col[rowi].rank == 14 - rowi for rowi in range(len(col))):
                counter += 1
            for rowi in reversed(range(len(col))):
                if col[rowi].rank < 0:
                    counter -= 1
                    continue
                if last_card == None:
                    last_card = col[rowi]
                elif last_card.rank + 1 == col[rowi].rank:
                    counter += 1
                    last_card = col[rowi]
                else:
                    break
        return counter

    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def find_movable_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        movable_cards = []
        for i, col in enumerate(self.columns):
            if len(col) == 9 and all(
                col[rowi].rank == col[rowi + 1].rank - 1 for rowi in range(len(col) - 1)
            ):
                continue
            for rowi in reversed(range(len(col))):
                if rowi == len(col) - 1:
                    movable_cards.append((i, rowi))
                    movable_cards.append((i, rowi))
                elif col[rowi].rank == col[rowi + 1].rank + 1:
                    movable_cards.pop()
                    movable_cards.append((i, rowi))
                else:
                    break
        return movable_cards

    def find_move_spaces(self, card_pos: tuple[int, int]) -> list[tuple[int, int]]:
        # returns col index and row index
        move_spaces = []
        card = self.columns[card_pos[0]][card_pos[1]]
        is_single = card_pos[1] == len(self.columns[card_pos[0]]) - 1
        is_valid = card.rank > 0
        for i, col in enumerate(self.columns):
            if len(col) == 9 and all(
                col[rowi].rank == col[rowi + 1].rank - 1 for rowi in range(len(col) - 1)
            ):
                continue
            if len(col) == 0 and card_pos[1] == 0:
                continue
            if len(col) == 0:
                move_spaces.append((i, len(col)))
            elif col[-1].rank < 0:
                continue
            elif is_single and is_valid:
                move_spaces.append((i, len(col) - 1))
            elif col[-1].rank - 1 == card.rank:
                move_spaces.append((i, len(col) - 1))
        return move_spaces

    def perform_move(self, from_pos: tuple[int, int], to_pos: int) -> State:
        new_state = State(self.columns)
        cards = new_state.columns[from_pos[0]][from_pos[1] :]
        new_state.columns[from_pos[0]] = new_state.columns[from_pos[0]][: from_pos[1]]
        cards[0] = Card(cards[0].rank)
        if (
            len(new_state.columns[to_pos]) > 0
            and new_state.columns[to_pos][-1].rank != cards[0].rank + 1
        ):
            cards[0].rank = -abs(cards[0].rank)
        if (
            len(new_state.columns[to_pos]) == 0
            or new_state.columns[to_pos][-1].rank == cards[0].rank + 1
        ):
            cards[0].rank = abs(cards[0].rank)
        new_state.columns[to_pos].extend(cards)
        return new_state


class Game:
    def __init__(self, state: State):
        self.starter = state

    def priority_queue(self):
        # visited is a map from target state to source state and the action required to get from source to target in format from col from row to col to row
        visited: dict[State, tuple[State, tuple[int, int, int, int]] | None] = {self.starter: None}
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
                        visited[new_state] = (state, (movable[0], movable[1], moveto[0], moveto[1]))
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
