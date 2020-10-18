from ankipandas import Collection
import networkx as nx
import matplotlib.pyplot as plt

col = Collection("/home/stephen/.local/share/Anki2/", user="Stephen Mwangi")

decks = {}
for card in col.cards.to_numpy():
    if card[0] in decks:
        continue
    try:
        if card[13] == "Miscellaneous::English":
            continue
        else:
            idx = card[13].rindex("::") + 2
            decks[card[0]] = '-'.join(card[13][idx:].split(" ")).lower()
    except ValueError:
        decks[card[0]] = card[13].lower()

color_code, subjects, subjects_rank = {}, {}, {}
with open("color-code.txt", "r") as f:
    lines = f.readlines()
    color_code['default'] = lines[0].split(',')[1].strip()
    for line in lines[1:]:
        d = line.split(',')
        for tag in d[2:]:
            color_code[tag.strip()] = d[1]
            subjects[tag.strip()] = d[0]

G = nx.DiGraph()
tags, node_sizes, node_colors, size_incr = [], [], [], 3

noteids = col.notes.id
tags_data = col.notes["ntags"]
col.db.close()

for noteid in noteids:
    if len(tags_data[noteid]) == 0:
        continue
    deck = decks[noteid]

    ntags = tags_data[noteid]

    if 'leech' in ntags:
        ntags.pop(ntags.index('leech'))
    for tag in ntags:
        if tag not in tags:
            tags.append(tag)
            try:
                node_colors.append(color_code[tag])
            except KeyError:
                print(f"Color code for the tag {tag} not found.")
                node_colors.append(color_code['default'])
            G.add_node(tag)
            node_sizes.append(0)
        node_sizes[tags.index(tag)] += size_incr

    for tag in ntags:
        if tag == deck:
            continue
        try:
            G[tag][deck]['weight'] += 1
        except KeyError:
            G.add_edge(tag, deck, weight = 1)

pr = nx.algorithms.link_analysis.pagerank_alg.pagerank(G)
sorted_pr = sorted(pr.items(), key=lambda kv: kv[1], reverse=True)

i, llen, backslash = 0, len(sorted_pr), '\n'
f = open("page-rank.txt", "w")
for i in range(llen):
    try:
        subjects_rank[subjects[sorted_pr[i][0]]] += round(sorted_pr[i][1] * 1000, 4)
    except KeyError:
        subjects_rank[subjects[sorted_pr[i][0]]] = round(sorted_pr[i][1] * 1000, 4)
    f.write(f"{i + 1} {sorted_pr[i][0]} {round(sorted_pr[i][1] * 1000, 4)}{backslash if i != llen - 1 else ''}")
f.write("\n\nTotal: " + str(sorted(subjects_rank.items(), key=lambda kv: kv[1], reverse=True)))
f.close()

fig = plt.gcf()
fig.set_size_inches(13.66, 6.43)
nx.nx_pydot.graphviz_layout(G)
nx.draw(G, pos = nx.nx_pydot.graphviz_layout(G), node_size = node_sizes, with_labels = True, font_size = 7, node_color = node_colors, edge_color = "#cccccc")
fig.savefig("knowledge-graph.png", dpi=100)
plt.show()