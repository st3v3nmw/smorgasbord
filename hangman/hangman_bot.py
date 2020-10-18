from random import choice, shuffle
from collections import Counter
from selenium.webdriver import Firefox, ActionChains
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from lib import Trie

"""
this bot plays the untimed hangman game on https://hangmanwordgame.com/?fca=1&success=0#/
"""

def wait(browser, method, name):
    try:
        element_present = EC.presence_of_element_located((method, name))
        WebDriverWait(browser, 5).until(element_present)
    except TimeoutException:
        print("Timed out waiting for page to load")

browser = Firefox()
browser.get("https://hangmanwordgame.com/?fca=1&success=0#/")

wait(browser, By.CLASS_NAME, 'profile-1head')
browser.execute_script("document.getElementsByClassName('profile-1head')[1].click()")

alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

wait(browser, By.CLASS_NAME, 'current-word')
curr = browser.execute_script("document.getElementsByClassName('current-word')")

action = ActionChains(browser)

trie = Trie("TWL06.txt")

while True:
    action_letters = browser.find_elements_by_class_name('letter-2')
    guessable = list(alphabet)
    shuffle(guessable)
    word = browser.find_element_by_class_name('current-word').text

    f = 0
    for i in range(26):
        possible = trie.query(word, dict.fromkeys(guessable, 26))
        if len(possible) == 1:
            guess = choice(possible[0])
            while guess not in guessable:
                guess = choice(possible[0])
        else:
            guess = "+"
            counter = Counter(''.join(possible))
            while guess not in guessable:
                try:
                    guess = counter.most_common()[0][0]
                    counter.pop(guess)
                except IndexError:
                    print(counter)
                    raise
        guessable.remove(guess)

        print(f"{''.join(word)}, {len(possible)} possible words, {f} fails ==> {guess}")
        action.move_to_element_with_offset(action_letters[alphabet.index(guess)], 0, 0)
        action_letters[alphabet.index(guess)].click()

        w1 = browser.find_element_by_class_name('current-word').text

        if w1 == word:
            f += 1

        word = w1

        if word.count('_') == 0:
            print(f"{word} 😝\n") # successfully found the word
            sleep(2) # wait for webpage to update to avoid race conditions
            break
