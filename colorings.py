"""
usage: colorings <file>

Program reads a graph coloring problem from file given by command line argument.
Prints all solutions satisfying constraints.
Draws all solutions satisfying constraints.
"""

import sys
import os
import matplotlib.pyplot as plt
import networkx as nx
import colortrade_tools as ct

g = ct.EdgeColoringInstance.from_json(sys.argv[1])
sols = g.solve()

print(f"Found {len(sols)} colorings:")
for sol in sols:
    print(sol)

# Display solutions
g.draw_colorings(sols)
plt.gcf().canvas.manager.set_window_title("All colorings")
plt.show(block=False)

# Find the color trade graph and show it
tg = ct.build_trade_graph(sols)
plt.figure(num = "Color trade graph")
nx.draw(tg, with_labels=True)
plt.show()
