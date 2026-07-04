import os
import json
import heapq

class Card:
    def __init__(self, suit: str | None = None, rank: int | None = None):
        self.rank = rank
        self.suit = suit

    @staticmethod
    def from_str(s: str) -> Card:
        c = Card()
        c.suit = s[0]
        if len(s) == 1:
            return c
        else:
            c.rank = int(s[1:])
            return c

    def __str__(self):
        return self.suit + (str(self.rank) if self.rank is not None else "")

    def pretty_str(self):
        pstr = ""
        if self.suit in ["R", "D", "H"]:
            pstr += "\033[91m"
        else:
            pstr += "\033[94m"
        if self.is_suit_card():
            pstr += self.suit
        if self.is_rank_card():
            pstr += str(self.rank)
        pstr += "\033[0m"
        return pstr

    def is_rank_card(self):
        return self.rank is not None

    def is_suit_card(self):
        return self.rank is None

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))


class State:
    def __init__(self, cards: list[list[Card]], space: Card | None):
        self.cards: list[list[Card]] = []
        for col in cards:
            self.cards.append(col.copy())
        self.space = space

    @staticmethod
    def from_str(s: list[list[str]]):
        cards = []
        for col in s:
            cards.append([])
            for cstr in col:
                cards[-1].append(Card.from_str(cstr))
        return State(cards, None)

    def pretty_str(self):
        pstr = ""
        max_row = max([len(col) for col in self.cards])
        for rowi in range(max_row):
            for col in self.cards:
                if len(col) >= rowi + 1:
                    pstr += col[rowi].pretty_str()
                pstr += "\t"
            pstr += "\n"
        pstr += f"space: {self.space.pretty_str() if self.space is not None else 'None'}"
        return pstr

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        if self.space != other.space:
            return False
        for coli in range(len(self.cards)):
            if len(self.cards[coli]) != len(other.cards[coli]):
                return False
            for rowi in range(len(self.cards[coli])):
                if self.cards[coli][rowi] != other.cards[coli][rowi]:
                    return False
        return True

    def __hash__(self):
        return hash((self.space, tuple(tuple(col) for col in self.cards)))

    def is_win(self):
        if self.space is not None:
            return False
        for col in self.cards:
            if len(col) not in [0, 4, 5]:
                return False
            if (len(col) == 4 and
                    (any(card.is_rank_card() for card in col) or
                     any(card.suit != col[0].suit for card in col))):
                return False
            if (len(col) == 5 and
                    (any(card.is_suit_card() for card in col) or
                     any(col[rowi].rank - 1 != col[rowi + 1].rank for rowi in range(4)))):
                return False
        return True
    
    def win_estimate(self):
        counter = 0
        if self.space is not None:
            counter -= 1
        for col in self.cards:
            if len(col) not in [0, 4, 5]:
                counter -= 1
            elif (len(col) == 4 and
                    (any(card.is_rank_card() for card in col) or
                     any(card.suit != col[0].suit for card in col))):
                counter -= 1
            elif (len(col) == 5 and
                    (any(card.is_suit_card() for card in col) or
                     any(col[rowi].rank - 1 != col[rowi + 1].rank for rowi in range(4)))):
                counter -= 1
        return counter
    
    def __lt__(self, other: State):
        return self.win_estimate() > other.win_estimate()

    def find_movable_cards(self) -> list[tuple[int, int]]:
        # returns col index and row index
        # -1 means space
        movable_cards = []
        if self.space is not None:
            movable_cards.append((-1, -1))
        for coli in range(len(self.cards)):
            col = self.cards[coli]
            if (len(col) == 4 and col[0].is_suit_card() and
                    col[0].suit == col[1].suit and
                    col[0].suit == col[2].suit and
                    col[0].suit == col[3].suit):
                continue
            if (len(col) == 5 and all(card.is_rank_card() for card in col) and all(
                    col[rowi].rank - 1 == col[rowi + 1].rank for rowi in range(4))):
                continue
            for rowi in reversed(range(len(self.cards[coli]))):
                if rowi == len(col) - 1:
                    movable_cards.append((coli, rowi))
                elif (col[rowi].is_rank_card() and col[rowi + 1].is_rank_card() and
                      col[rowi].rank - 1 == col[rowi + 1].rank and
                      col[rowi].suit != col[rowi + 1].suit):
                    movable_cards.append((coli, rowi))
                elif (col[rowi].is_suit_card() and col[rowi + 1].is_suit_card() and
                      col[rowi].suit == col[rowi + 1].suit):
                    movable_cards.append((coli, rowi))
        return movable_cards

    def find_move_spaces(self, card_pos: tuple[int, int]) -> list[tuple[int, int]]:
        # returns col index and row index of where the card can be moved to
        # -1 means space
        a_spaces: list[tuple[int, int]] = []
        if self.space is None and card_pos[1] == len(self.cards[card_pos[0]]) - 1:
            a_spaces.append((-1, -1))
        if card_pos[0] == -1:
            card = self.space
        else:
            card = self.cards[card_pos[0]][card_pos[1]]
        for coli in range(len(self.cards)):
            col = self.cards[coli]
            if len(col) == 0:
                a_spaces.append((coli, len(col)))
            elif (card.is_suit_card() and col[-1].is_suit_card() and
                  card.suit == col[-1].suit):
                a_spaces.append((coli, len(col) - 1))
            elif (card.is_rank_card() and col[-1].is_rank_card() and
                  card.rank == col[-1].rank - 1 and
                  card.suit != col[-1].suit):
                a_spaces.append((coli, len(col) - 1))
        return a_spaces

    def perform_move(self, from_pos: tuple[int, int], to_pos: int) -> State:
        new_state = State(self.cards, self.space)
        if from_pos[0] == -1:
            cards = [new_state.space]
            new_state.space = None
        else:
            cards = new_state.cards[from_pos[0]][from_pos[1]:]
            new_state.cards[from_pos[0]] = new_state.cards[from_pos[0]][:from_pos[1]]
        if to_pos == -1:
            new_state.space = cards[0]
        else:
            new_state.cards[to_pos].extend(cards)
        return new_state


class Game:
    def __init__(self, state: State):
        self.starter = state

    def DFS(self):
        # visited is a map from target state to source state and the action required to get from source to target in format from col from row to col to row
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
            for movable in state.find_movable_cards():
                if found:
                    break
                for moveto in state.find_move_spaces(movable):
                    if found:
                        break
                    new_state = state.perform_move(movable, moveto[0])
                    if new_state not in visited:
                        visited[new_state] = (state, (movable[0], movable[1], moveto[0], moveto[1]))
                        queue.append(new_state)
                        if new_state.is_win():
                            found = True
                            found_state = new_state
        path = [visited[found_state]]
        while visited[path[-1][0]] is not None:
            path.append(visited[path[-1][0]])
        path.reverse()
        return path, states_explored

    def BFS(self):
        # visited is a map from target state to source state and the action required to get from source to target in format from col from row to col to row
        visited: dict[State, tuple[State, tuple[int, int, int, int]] | None] = {self.starter: None}
        queue: list[State] = [self.starter]

        states_explored = 0
        found = False
        found_state = None

        while len(queue) > 0:
            if found:
                break
            state = queue[0]
            queue = queue[1:]
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
                        queue.append(new_state)
                        if new_state.is_win():
                            found = True
                            found_state = new_state
        path = [visited[found_state]]
        while visited[path[-1][0]] is not None:
            path.append(visited[path[-1][0]])
        path.reverse()
        return path, states_explored

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