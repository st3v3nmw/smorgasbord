import heapq
from collections import defaultdict
from binascii import hexlify, unhexlify

class HuffmanTree:
    class Node:
        def __init__(self):
            self.value = None
            self.left = None
            self.right = None

        def insert(self, data, i, value):
            if len(data) == i:
                self.value = value
                return

            if data[i] == '0':
                if self.left is None:
                    self.left = HuffmanTree.Node()
                self.left.insert(data, i+1, value)
            else:
                if self.right is None:
                    self.right = HuffmanTree.Node()
                self.right.insert(data, i+1, value)

        def traverse(self, data, i):
            if len(data) == i:
                return self.value
            if data[i] == '0':
                return self.left.traverse(data, i+1)
            else:
                return self.right.traverse(data, i+1)
        

    def __init__(self, mapped):
        self.root = self.Node()
        for key in mapped:
            self.root.insert(mapped[key], 0, key)

    def traverse(self, data):
        return self.root.traverse(data, 0)

def encode(frequency):
    heap = [[weight, [symbol, '']] for symbol, weight in frequency.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    return sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))

def compress(data, codes):
    length = bin(len(codes))[2:]
    result = ['0' * (8 - len(length)) + length]
    for key in codes:
        result.append('0' * (8 - len(bin(ord(key))[2:])) + bin(ord(key))[2:])
        length = bin(len(codes[key]))[2:]
        result.append('0' * (4 - len(length)) + length)
        result.append(codes[key])
    for symbol in data:
        result.append(codes[symbol])
    return ''.join(result)

f = open('input.txt', 'r')
data = f.read() + "\n"
frequency = defaultdict(int)
for symbol in data:
    frequency[symbol] += 1

mapped = {}
huff = encode(frequency)
for p in huff:
    mapped[p[0]] = p[1]

bin_data = ''.join(f"{ord(x):08b}" for x in data)
compressed = compress(data, mapped)
print(len(compressed))

# write compressed to file
with open("compressed.txt", 'wb') as f:
    c = [int(compressed[i:i+8], 2) for i in range(0, len(compressed), 8)]
    f.write(''.join(chr(x) for x in c).encode('charmap'))

# decode file
decoded_map = {}
with open("compressed.txt", 'rb') as f:
    d = [x for x in f.read()]
    data = ['0' * (8 - len(bin(d[i])[2:])) + bin(d[i])[2:] for i in range(len(d) - 1)]
    data.append(bin(d[len(d) - 1])[2:])
    string = ''.join(data)
    print(string)

    n = int(string[:8], 2)

    idx = 8
    for _ in range(n):
        length = int(string[idx+8:idx+12], 2)
        decoded_map[chr(int(string[idx:idx + 8], 2))] = string[idx + 12: idx + 12 + length]
        idx = idx + 12 + length
        
    print(len(mapped), mapped)
    print(len(decoded_map), decoded_map)

    tree = HuffmanTree(decoded_map)

    sub = ''
    for char in string[idx:]:
        sub += char
        try:
            last = tree.traverse(sub)
        except AttributeError:
            sub = char
            print(last, end="")
print()
