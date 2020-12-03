from lib import Stack, HTMLNode, CSSNode, parseTagName

FILENAME = "source.html"

with open(FILENAME, 'r') as f:
    raw = f.readlines()
    code = []
    for line in raw:
        code.append(line.strip())
    code = ''.join(code)

stack = Stack()
parentsTracker = Stack()
parentsTracker.push(HTMLNode("root", "", "", [], {}))
nodes = []
notParents = ['img', 'link', 'input']
scripts, stylesheets = [], []
favicon = []

# parse HTML
startTag, endTag = False, False
innerText = []
for i in range(len(code)):
    char = code[i]
    if char == '<' and code[i + 1] == "/":
        parentsTracker.pop()
        startTag, endTag = False, True
        if len(innerText) > 0:
            nodes[len(nodes) - 1].innerText = ''.join(innerText)
            innerText = []
    elif char == '<':
        startTag, endTag = True, False
        stack.push(char)
        if len(innerText) > 0:
            nodes[len(nodes) - 1].innerText = ''.join(innerText)
            innerText = []
    elif char == '>' and startTag:
        tag = []
        while stack.top != '<':
            tag.append(stack.pop())
        stack.pop()
        tagName =  ''.join(reversed(tag))
        tagName, idName, classes, style, other = parseTagName(tagName)
        
        if tagName == 'script':
            scripts.append(other['src'])
        elif tagName == 'link':
            stylesheets.append(other['href'])
        else:
            new_node = HTMLNode(tagName, idName, classes, style, other)
            parentsTracker.top.addChild(new_node)
            nodes.append(new_node)
            if tagName not in notParents:
                parentsTracker.push(nodes[len(nodes) - 1])
            startTag, endTag = False, False
    elif startTag:
        stack.push(char)
    elif not startTag and not endTag:
        innerText.append(char)

# parse CSS stylesheets
stack = Stack()
cssNodes = []
for stylesheet in stylesheets:
    with open(stylesheet, 'r') as f:
        raw = f.readlines()
        code = []
        for line in raw:
            code.append(line.strip())
        code = ''.join(code)

    properties, values = [], []
    for char in code:
        if char == ' ':
            continue
        elif char == '{':
            name = []
            while stack.top:
                name.append(stack.pop())
            name = ''.join(reversed(name))
            typeName = "class" if name[0] == '.' else "id" if name[0] == '#' else "tag"
            if name[0] == '.' or name[0] == '#':
                name = name[1:]
        elif char == ':':
            propertyName = []
            while stack.top:
                propertyName.append(stack.pop())
            properties.append(''.join(reversed(propertyName)))
        elif char == ';':
            value = []
            while stack.top:
                value.append(stack.pop())
            values.append(''.join(reversed(value)))
        elif char == "}":
            style = [(properties[i], values[i]) for i in range(len(properties))]
            cssNodes.append(CSSNode(name, typeName, style))
            properties, values = [], []
        else:
            stack.push(char)

cssNodes.sort(key = lambda node: node.priority)
for cssNode in cssNodes:
    for node in nodes:
        if cssNode.typeName == 'tag':
            if node.tag == cssNode.name:
                node.setStyle(cssNode.style)
        elif cssNode.typeName == 'class':
            if cssNode.name in node.classes:
                node.setStyle(cssNode.style)
        else:
            if cssNode.name == node.id:
                node.setStyle(cssNode.style)

for node in nodes:
    print(node.tag, node.childrenTags, node.innerText, node.style, node.id, node.classes, node.other)