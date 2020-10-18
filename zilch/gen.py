from random import random, choices

p = 100
new = lambda x: x + 5 * choices([random(), -1 * random()])[0]

with open("in.txt", "w") as f:
    for _ in range(1000):
        p = new(p)
        if p < 0:
            p = 1
        f.write(str(p) + "\n")