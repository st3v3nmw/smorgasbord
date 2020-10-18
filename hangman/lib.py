from copy import deepcopy

class Trie:
    class Node:
        def __init__(self):
            self.children = {}
            self.word_finished = False
            self.is_word = False

    def __init__(self, path):
        self.root = self.Node()
        with open(path, 'r') as f:
            wordlist = f.readlines()
            for word in wordlist:
                self.add(word.strip())
        self.words = []

    def add(self, word):
        node = self.root
        length = len(word)
        for i in range(length):
            char = word[i]
            if char in node.children:
                node = node.children[char]
            else:
                new_node = self.Node()
                node.children[char] = new_node
                node = new_node
            if length - 1 == i: node.is_word = True
        node.word_finished = True

    def query(self, q, letters):
        n_spaces = q.count('_')
        self.words = []
        self.getPartWord(self.root, q, letters, n_spaces, 0, "")
        return self.words

    def getPartWord(self, node, q, letters, n_spaces, position, word):
        if position == len(q):
            if node.is_word:
                self.words.append(word)
            return
        if q[position] == '_':
            for char in letters.keys():
                if letters[char] and char in node.children:
                    toPass = deepcopy(letters)
                    toPass[char] -= 1
                    self.getPartWord(node.children[char], q, toPass, n_spaces - 1, position + 1, word + char)
        else:
            for char in node.children.keys():
                if q[position] == char:
                    self.getPartWord(node.children[char], q, deepcopy(letters), n_spaces, position + 1, word + char)

    def verifyWord(self, word):
        node = self.root
        for position in range(len(word)):
            if word[position] in node.children:
                node = node.children[word[position]]
            else: return False
        return node.is_word
