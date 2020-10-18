from random import choice, shuffle
from collections import Counter
from lib import Trie

alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

FILENAME = "TWL06.txt" # dictionary file (each word should be on a new line)
trie = Trie(FILENAME)
f = open(FILENAME, 'r')
words = f.readlines()

r = choice(words).strip()

llen = len(r)

word = ["_"] * llen

print(f"Random word is {r}")

guessable = list(alphabet)
shuffle(guessable)

f = 0
for i in range(26):
    possible = trie.query(word, dict.fromkeys(guessable, 26))
    if len(possible) == 1:
        print(f"{possible[0]}? :)")
        print(f"{i + 1} tries")
        break
    guess = "+"
    counter = Counter(''.join(possible))
    while guess not in guessable:
        guess = counter.most_common()[0][0]
        counter.pop(guess)
    guessable.remove(guess)
    print(f"{''.join(word)}, {len(possible)} possible words, {f} fails ==> {guess}")
    if guess in r:
        pos = [i for i in range(llen) if r[i] == guess]
        for p in pos:
            word[p] = guess
    else:
        f += 1
