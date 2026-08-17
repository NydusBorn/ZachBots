import heapq
import json
import os
from typing import Any


class Card:
    def __init__(self, suit: str | None = None, rank: int | None = None):
        self.rank = rank
        self.suit = suit

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
            case x:
                c.rank = int(x)
        return c

    def __str__(self):
        return self.suit + (str(self.rank) if self.rank is not None else "")

    def pretty_str(self):
        pstr = ""
        if self.suit == "R":
            pstr += "\033[91m"
        else:
            pstr += "\033[94m"
        pstr += str(self.rank)
        pstr += "\033[0m"
        return pstr

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))


class State:
    def __init__(
        self,
        columns: list[list[Card]],
        space: Card | int | None,
        stack: list[Card],
        suits: list[Card | None],
    ):
        self.columns: list[list[Card]] = []
        for col in columns:
            self.columns.append(col.copy())
        self.space = space
        self.stack = stack.copy()
        self.suits = suits.copy()

    @staticmethod
    def from_str(s: dict[str, Any]):
        columns = []
        space = None
        stack = []
        suits = []
        for col in s["columns"]:
            columns.append([])
            for cstr in col:
                columns[-1].append(Card.from_str(cstr))
        for cstr in s["stack"]:
            stack.append(Card.from_str(cstr))
        if s["space"] == "?":
            space = 0
        elif s["space"] != "":
            space = Card.from_str(s["space"])
        for suit in s["suits"]:
            if suit == "":
                suits.append(None)
            else:
                suits.append(Card.from_str(suit))
        return State(columns, space, stack, suits)

    def pretty_str(self):
        pstr = ""
        max_row = max([len(col) for col in self.columns])
        for rowi in range(max_row):
            for col in self.columns:
                if len(col) >= rowi + 1:
                    pstr += col[rowi].pretty_str()
                pstr += "\t"
            pstr += "\n"
        if self.space is not None:
            if self.space is int:
                pstr += f"space: ?"
            else:
                pstr += f"space: {self.space.pretty_str()}"
        else:
            pstr += f"space: None"
        pstr += "\nstack:"
        for c in self.stack:
            pstr += f" {c.pretty_str()}"
        pstr += "\n suits:"
        for s in self.suits:
            if s is None:
                pstr += f" None"
            else:
                pstr += f" {s.pretty_str()}"
        return pstr

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        if self.space != other.space:
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
        for si in range(len(self.suits)):
            if self.suits[si] != other.suits[si]:
                return False
        return True

    def __hash__(self):
        return hash((self.space, tuple(tuple(col) for col in self.columns), tuple(self.stack), tuple(self.suits)))

    def is_win(self):
        for suitc in self.suits:
            if suitc is None or suitc.rank != 13:
                return False
        return True

    def win_estimate(self):
        counter = 0
        last_card = None
        for col in self.columns:
            stack_len = 0
            for rowi in reversed(range(len(col))):
                stack_len += 1
                if last_card is None:
                    last_card = col[rowi]
                    counter += 13 - last_card.rank
                    continue
                if col[rowi].rank == last_card.rank + 1 and col[rowi].suit != last_card.suit:
                    counter += 13 - col[rowi].rank
                    last_card = col[rowi]
                else:
                    stack_len -= 1
                    counter += stack_len - len(col)
                    break
            last_card = None
        return counter

    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def find_movable_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1 means space
        # -2 means in col means stack, row means the card in stack
        movable_cards = []
        if self.space is Card:
            movable_cards.append((-1, -1))
        if len(self.stack) > 0:
            movable_cards.append((-2, len(self.stack) - 1))
        for coli in range(len(self.columns)):
            col = self.columns[coli]
            for rowi in reversed(range(len(self.columns[coli]))):
                if rowi == len(col) - 1:
                    movable_cards.append((coli, rowi))
                elif (
                    col[rowi].rank - 1 == col[rowi + 1].rank
                    and col[rowi].suit != col[rowi + 1].suit
                ):
                    movable_cards.append((coli, rowi))
                else:
                    break
        return movable_cards

    def find_move_spaces(self, card_pos: tuple[int, int]) -> list[tuple[int, int]]:
        # returns col index and row index of where the card can be moved to
        # -1 means space
        a_spaces: list[tuple[int, int]] = []
        if self.space is None and card_pos[0] >= 0 and card_pos[1] == len(self.columns[card_pos[0]]) - 1:
            a_spaces.append((-1, -1))
        if self.space is None and card_pos[0] == -2:
            a_spaces.append((-1, -1))
        if card_pos[0] == -1:
            card = self.space
        elif card_pos[0] == -2:
            card = self.stack[-1]
        else:
            card = self.columns[card_pos[0]][card_pos[1]]
        for coli in range(len(self.columns)):
            col = self.columns[coli]
            if len(col) == 0 and card_pos[0] >= 0 and card_pos[1] == 0:
                continue
            if len(col) == 0:
                a_spaces.append((coli, len(col)))
            elif (
                card.rank == col[-1].rank - 1
                and card.suit != col[-1].suit
            ):
                a_spaces.append((coli, len(col) - 1))
        return a_spaces

    def perform_move(self, from_pos: tuple[int, int], to_pos: int) -> State:
        new_state = State(self.columns, self.space, self.stack, self.suits)
        if from_pos[0] == -1:
            cards = [new_state.space]
            new_state.space = None
        elif from_pos[0] == -2:
            cards = [new_state.stack.pop()]
        else:
            cards = new_state.columns[from_pos[0]][from_pos[1] :]
            new_state.columns[from_pos[0]] = new_state.columns[from_pos[0]][: from_pos[1]]
        if to_pos == -1:
            new_state.space = cards[0]
        else:
            new_state.columns[to_pos].extend(cards)
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
            if found or states_explored == 1000:
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
        best_state = self.starter
        for st in visited:
            if st.win_estimate() > best_state.win_estimate():
                best_state = st
        path = [visited[best_state]]
        while path[-1] is not None and visited[path[-1][0]] is not None:
            path.append(visited[path[-1][0]])
        path.reverse()
        if path[0] is None: path = []
        return path, states_explored


if __name__ == "__main__":
    for filename in os.listdir("saves"):
        if filename.endswith(".json") and filename.__contains__("3"):
            json_name = filename.replace(".png", ".json")
            json_content = json.load(open(f"saves/{json_name}"))
            state = State.from_str(json_content)
            game = Game(state)
            print(state.pretty_str())
            print(state.win_estimate())
            print("Priority Queue")
            res = game.priority_queue()
            print(f"path len = {len(res[0])}")
            print(res[0][-1][0].pretty_str())
            print(f"explored = {res[1]}")
            print(res[0][-1][0].win_estimate())
