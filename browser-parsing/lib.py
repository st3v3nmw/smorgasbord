class Stack:
    def __init__(self):
        self.data = []

    def push(self, element):
        self.data.append(element)
    
    def pop(self):
        return self.data.pop()

    def is_empty(self):
        return len(self.data) == 0

    @property
    def top(self):
        if self.is_empty():
            return None
        return self.data[len(self.data) - 1]

class HTMLNode:
    def __init__(self, tag, idName, classes, style, other):
        self.tag = tag
        self.innerText = ""
        self.children = []
        self.style = {}
        self.setStyle(style)
        self.classes = classes
        self.id = idName
        self.other = other

    def addChild(self, child):
        self.children.append(child)

    def setStyle(self, styles):
        for style in styles:
            self.style[style[0]] = style[1]

    @property
    def childrenTags(self):
        tags = []
        for child in self.children:
            tags.append(child.tag)
        return tags

class CSSNode:
    priorities = {"tag": 0, "class": 1, "id": 2}
    def __init__(self, name, typeName, style):
        self.name = name
        self.typeName = typeName
        self.priority = self.priorities[typeName]
        self.style = style

def parseInTagCSS(string):
    string = string.replace(":", ";")
    tokens = string.split(';')
    parsed = []
    i = 0
    while i < len(tokens) - 1:
        parsed.append((tokens[i].strip(), tokens[i + 1].strip()))
        i += 2        
    return parsed

def parseTagName(tagName):
    indexes = []
    other = {}
    style = parseInTagCSS(extract(tagName, "style=", 7, indexes))
    classes = extract(tagName, "class=", 7, indexes).split()
    idName = extract(tagName, "id=", 4, indexes)
    src = extract(tagName, "src=", 5, indexes)
    if src != '':
        other['src'] = src
    href = extract(tagName, "href=", 6, indexes)
    if href != '':
        other['href'] = href
    typeName = extract(tagName, "type=", 6, indexes)
    if typeName != '':
        other['type'] = extract(tagName, "type=", 6, indexes)
    rel = extract(tagName, "rel=", 5, indexes)
    if src != '':
        other['rel'] = rel

    # tag
    if len(indexes) > 0:
        tagName = tagName[:min(indexes)-1]

    return tagName, idName, classes, style, other

def extract(string, query, offset, indexes):
    result = ""
    index = string.find(query)
    if index != -1:
        indexes.append(index)
        endTag = string.find("\"", index+offset)
        result = string[index+offset:endTag]
    return result