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
            case "A":
                c.rank = 1
            case "J":
                c.rank = 11
            case "Q":
                c.rank = 12
            case "K":
                c.rank = 13
            case x:
                c.rank = int(x)
        return c

    def score(self):
        return min(10, self.rank)

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
        stack: list[Card],
        score: int,
    ):
        self.columns: list[list[Card]] = []
        for col in columns:
            self.columns.append(col.copy())
        self.stack = stack.copy()
        self.score = score

    @staticmethod
    def from_str(s: list[list[str]]):
        columns = []
        for col in s:
            columns.append([])
            for cstr in col:
                columns[-1].append(Card.from_str(cstr))
        return State(columns, [], 0)

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        if self.score != other.score:
            return False
        if len(self.stack) != len(other.stack):
            return False
        for coli in range(len(self.columns)):
            if len(self.columns[coli]) != len(other.columns[coli]):
                return False
            for rowi in range(len(self.columns[coli])):
                if self.columns[coli][rowi] != other.columns[coli][rowi]:
                    return False
        for ci in range(len(self.stack)):
            if self.stack[ci] != other.stack[ci]:
                return False
        return True

    def __hash__(self):
        return hash(
            (
                tuple(tuple(col) for col in self.columns),
                tuple(self.stack),
                self.score,
            )
        )

    def running_score(self):
        counter = 0
        for card in self.stack:
            counter += card.score()
        return counter

    def is_win(self):
        if self.score < 61:
            return False
        for col in self.columns:
            if len(col) != 0:
                return False
        return True

    def win_estimate(self):
        return self.score

    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def find_act_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        active_cards = []
        for i, col in enumerate(self.columns):
            if len(col) != 0 and self.running_score() + col[-1].score() <= 31:
                active_cards.append((i, len(col) - 1))
        return active_cards

    def run_of_cards(self) -> int:
        def fits(ab: list[int])->bool:
            for i in range(len(ab) - 1):
                if ab[i+1] - ab[i] != 1:
                    return False
            return True
        if len(self.stack) < 3: return 0
        ranks = [c.rank for c in self.stack]
        for i in reversed(range(3, 8)):
            if len(ranks) >= i and fits(sorted(ranks[-i:])):
                return i
        return 0

    def perform_move(self, from_pos: tuple[int, int]) -> State:
        new_state = State(self.columns, self.stack, self.score)
        card = new_state.columns[from_pos[0]][from_pos[1]]
        new_state.columns[from_pos[0]] = new_state.columns[from_pos[0]][
            : from_pos[1]
        ]
        if len(new_state.stack) == 0 and card.rank == 11:
            new_state.score += 2
        if len(new_state.stack) > 0 and new_state.stack[-1] == card:
            new_state.score += 2
            if len(new_state.stack) > 1 and new_state.stack[-2] == card:
                new_state.score += 4
                if len(new_state.stack) > 2 and new_state.stack[-3] == card:
                    new_state.score += 6
        new_state.stack.append(card)
        if new_state.running_score() in [15, 31]:
            new_state.score += 2
        new_state.score += new_state.run_of_cards()
        return new_state

    def reset_stack(self) -> State:
        return State(self.columns, [], self.score)


class Game:
    def __init__(self, state: State):
        self.starter = state

    def priority_queue(self):
        # visited is a map from target state to source state and the action required to get from source to target in format from col from row to col to row
        visited: dict[State, tuple[State, tuple[int, int]] | None] = {
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
            active_cards = state.find_act_cards()
            if len(active_cards) == 0:
                new_state = state.reset_stack()
                if new_state not in visited:
                    visited[new_state] = (
                        state,
                        (-1, len(state.stack))
                    )
                    heapq.heappush(queue, new_state)
                    if new_state.is_win():
                        found = True
                        found_state = new_state
            else:
                for active in active_cards:
                    if found:
                        break
                    new_state = state.perform_move(active)
                    if new_state not in visited:
                        visited[new_state] = (
                            state,
                            (active[0], active[1]),
                        )
                        heapq.heappush(queue, new_state)
                        if new_state.is_win():
                            found = True
                            found_state = new_state
        path = [visited[found_state]]
        while path[-1] is not None and visited[path[-1][0]] is not None:
            path.append(visited[path[-1][0]])
        path.reverse()
        if path[0] is None:
            path = []
        return path, states_explored


if __name__ == "__main__":
    for filename in os.listdir("saves"):
        if filename.endswith(".json"):
            json_name = filename.replace(".png", ".json")
            json_content = json.load(open(f"saves/{json_name}"))
            state = State.from_str(json_content)
            game = Game(state)
            print(state.win_estimate())
            print("Priority Queue")
            res = game.priority_queue()
            print(f"path len = {len(res[0])}")
            print(f"explored = {res[1]}")
            print(res[0][-1][0].win_estimate())
