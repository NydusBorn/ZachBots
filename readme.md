This project provides a python bot to solve various games from zachtronics solitaire collection.

Bot difficulties (in order of completion):
- proletariat:
  - detection: relatively simple
  - solver: does require a priority queue in order to give close to optimal paths (the optimal path is somewhere around 30-35 moves, the solver produces 40-50), since simple DFS produces paths with lengths of 150+
- sigmars:
  - detection: inconvenient at best, fine tuning hell at worst
  - solver: all paths are length 28, so a simple DFS can suffice (in order to speed up search it is possible to use a notion of dead ends, since they are applicable in sigmars)
- sawayama:
  - detection: requires high-ish precision, since the detection runs multiple times per every action
  - solver: this one does not have reliable information from the start, since the stack contains 24 cards in unknown order, and the actual suites for the cards are also occluded when they are in columns. This is solved by using a win estimate that looks at how "orderly" the cards are layed out, and tries to maximise that "order". Since the suites are unknown and the stack exists, the solver takes a screenshot after every move, since the cards are put out of the game when they are not needed any longer
- cribbage:
  - detection: one of the simplest
  - solver: since the main purpose is to attain points, the priority is easy to set up. There isnt much room for error though, with the solver feasibly producing 65 points, of 61 required
- cluj:
  - detection: simplest one of them
  - solver: generally same difficulty as proletariat, though with less conditions, and a bigger emphasis on win estimations
- kabufuda:
  - detection: simple enough
  - solver: simplest conditions (since there are no ranks), and generally easier than proletariat
- shenzhen:
  - detection: uses color matching
  - solver: unlike sawayama, shenzhen has both convergence (cards that can be moved off the field since they have no use are automatically moved), and reliable information from the start, so unlike sawayama it allows to introduce wait action during solving, rather than using pure heuristics and taking screenshots at every action
