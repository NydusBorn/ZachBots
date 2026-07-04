This project provides a python bot to solve various games from zachtronics solitaire collection.

Bot difficulties:
- proletariat:
  - detection: relatively simple
  - solver: does require a priority queue in order to give close to optimal paths (the optimal path is somewhere around 30-35 moves, the solver produces 40-50), since simple DFS produces paths with lengths of 150+
- sigmars:
  - detection: inconvenient at best, fine tuning hell at worst
  - solver: all paths are length 28, so a simple DFS can suffice (in order to speed up search it is possible to use a notion of dead ends, since they are applicable in sigmars)