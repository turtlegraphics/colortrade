"""
usage: colorings <file>

Program reads a graph coloring problem from file given by command line argument.
Prints all solutions satisfying constraints.
Draws all solutions satisfying constraints.
"""

import sys
import os
import argparse
import matplotlib.pyplot as plt
import networkx as nx
import colortrade_tools as ct
from collections import Counter

def parse_args():
    parser = argparse.ArgumentParser(description="Process a graph file.")
    parser.add_argument("filename",
                        help="Input filename")
    parser.add_argument("-tradegraph",
                        action="store_true",
                        help="Show the color trade graph")
    parser.add_argument("-showall",
                        action="store_true",
                        help="Show all colorings")
    parser.add_argument("-latex",
                        type=int,
                        help="Print latex tikz code to draw the numbered coloring")
    
    return parser.parse_args()
args = parse_args()

g = ct.EdgeColoringInstance.from_json(args.filename)
sols = g.solve()
tg = ct.build_trade_graph(sols)
 
print("Color trade graph")
print("Total colorings (= # of vertices):", len(sols))
print("Total swaps (= # of edges):", tg.number_of_edges())
sizes = sorted((len(c) for c in nx.connected_components(tg)), reverse=True)
print("Number of components:", len(sizes))
print("Component sizes:", sizes)

print("Degree spectrum")
degs = [d for _, d in tg.degree()]
spectrum = Counter(degs)
for degree in sorted(spectrum):
    print(degree, ":", spectrum[degree])

# TeX output if requested
if args.latex is not None:
    if int(args.latex) not in range(len(sols)):
        print('latex:',args.latex,'is not a numbered coloring.')
    else:
        print(g.draw_latex(sols[int(args.latex)]))
    
# Display solutions
if args.showall:
    g.draw_colorings(sols)
    plt.gcf().canvas.manager.set_window_title("All colorings")
    plt.show()

# Find the color trade graph and show it
if args.tradegraph:
    plt.figure(num = "Color trade graph")
    nx.draw(tg, with_labels=True)
    plt.show()

