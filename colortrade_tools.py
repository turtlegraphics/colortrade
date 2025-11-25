"""
Graph edge-coloring utilities with per-vertex color constraints.

This module provides a class and some standalone functions:

    * class EdgeColoringInstance:
       Container for a graph edge-coloring instance:
        - an undirected graph G
        - per-vertex color constraints
        - an optional layout for drawing
       Methods:
       from_json()
       solve()
       draw_coloring()
       draw_colorings()
      
    * draw_all_edge_colorings(self.G, solutions, layout=self.layout, **kwargs)
                                                        
    * read_graph_json(path)
        Load a graph and per-vertex incident-color constraints from a
        human-readable JSON file.  The JSON format requires two keys:

            {
              "vertices": {
                "v1": ["colorA", "colorB", ...],
                "v2": ["colorC", "colorD", ...]
              },
              "edges": [
                ["v1", "v2"],
                ["v2", "v3"],
                ...
              ]
            }

        Vertex identifiers must be strings; colors may be any hashable
        objects (typically strings or integers).

    * all_edge_colorings_with_vertex_constraints(G, vertex_colors)
        Enumerate all proper edge colorings of an undirected graph G
        such that each vertex v uses *exactly* the set of colors listed
        in vertex_colors[v].  Properness means no two edges incident to
        a vertex may share the same color.  The function returns a list
        of dictionaries mapping edges (u, v) to chosen colors.

        Degree–color consistency is assumed:
            deg(v) == len(vertex_colors[v])
        If violated, the solver will raise an error.

    • draw_edge_colorings(G, coloring, …)
        Visualization helper that draws a single edge-colored graph using
        matplotlib.  Colors may be integers (mapped to a colormap) or any
        matplotlib-accepted color strings.

    • draw_all_edge_colorings(G, solutions, ...)

Intended Use
------------
These functions support experiments with constrained edge-colorings,
constraint satisfaction, puzzle generation, and combinatorial research.
Graphs are read from a lightweight JSON format, processed through a
custom backtracking solver, and displayed with NetworkX.

Dependencies
------------
    • networkx
    • matplotlib
    • math
    • json (standard library)

Example
-------
    >>> G, vertex_colors = read_graph_json("example.json")
    >>> solutions = all_edge_colorings_with_vertex_constraints(G, vertex_colors)
    >>> draw_edge_coloring(G, solutions[0])

This module is self-contained and does not modify NetworkX objects
beyond storing color labels in a returned dictionary.

Basically this was written by ChatGPT 5.1, with a little help from Bryan Clair.
"""

import math
import matplotlib.pyplot as plt
import json
import networkx as nx
from itertools import combinations

def all_edge_colorings_with_vertex_constraints(G, vertex_colors):
    """
    Enumerate all proper edge colorings of G such that for each vertex v:
      - incident edges use exactly the colors in vertex_colors[v]
      - no two edges incident to v share a color (proper edge-coloring condition)
    
    Parameters
    ----------
    G : networkx.Graph
        Simple undirected graph.
    vertex_colors : dict
        Mapping v -> iterable of colors. Colors are any hashable objects.
        Must satisfy: degree(v) == len(set(vertex_colors[v])).
    
    Returns
    -------
    list of dict
        Each element is a dict mapping edges (u, v) to colors.
        Edges are keyed exactly as in G.edges().
    """

    # Basic sanity checks
    if set(G.nodes()) != set(vertex_colors.keys()):
        raise ValueError("vertex_colors must define a color list for every vertex in G")

    allowed = {v: set(cs) for v, cs in vertex_colors.items()}

    # Degree / constraint consistency
    for v in G.nodes():
        deg = G.degree(v)
        colors_v = allowed[v]
        if len(colors_v) != len(vertex_colors[v]):
            raise ValueError(f"Duplicate colors in constraint for vertex {v}")
        if deg != len(colors_v):
            raise ValueError(
                f"Degree/constraint mismatch at v={v}: deg={deg}, "
                f"|colors|={len(colors_v)}"
            )

    edges = list(G.edges())
    m = len(edges)

    # Per-vertex bookkeeping
    deg = dict(G.degree())
    remaining_colors = {v: set(allowed[v]) for v in G.nodes()}
    used_colors = {v: set() for v in G.nodes()}
    colored_incident = {v: 0 for v in G.nodes()}  # how many incident edges are already colored

    edge_colors = {}  # (u, v) -> color
    solutions = []

    def backtrack(edge_index):
        if edge_index == m:
            # All edges are colored; check that every vertex has used all its colors
            if all(len(remaining_colors[v]) == 0 for v in G.nodes()):
                solutions.append(dict(edge_colors))
            return

        u, v = edges[edge_index]

        # Available colors for this edge = colors still unused at both endpoints
        possible_colors = remaining_colors[u] & remaining_colors[v]
        if not possible_colors:
            return  # dead end

        for c in possible_colors:
            # Properness is already guaranteed by remaining_colors/used_colors:
            # we never allow a color already used at a vertex.
            # Assign c to edge (u, v)
            edge_key = (u, v)
            edge_colors[edge_key] = c

            used_colors[u].add(c)
            used_colors[v].add(c)
            remaining_colors[u].remove(c)
            remaining_colors[v].remove(c)
            colored_incident[u] += 1
            colored_incident[v] += 1

            # Forward-check: there must be enough incident edges left to place all remaining colors
            ok = True
            for w in (u, v):
                uncolored_edges_at_w = deg[w] - colored_incident[w]
                if len(remaining_colors[w]) > uncolored_edges_at_w:
                    ok = False
                    break

            if ok:
                backtrack(edge_index + 1)

            # Undo assignment
            colored_incident[u] -= 1
            colored_incident[v] -= 1
            remaining_colors[u].add(c)
            remaining_colors[v].add(c)
            used_colors[u].remove(c)
            used_colors[v].remove(c)
            del edge_colors[edge_key]

    backtrack(0)
    return solutions

def draw_edge_coloring(G, coloring, layout=None, node_size=600, width=3):
    """
    Draw a graph G with edges colored according to the dictionary `coloring`.

    Parameters
    ----------
    G : networkx.Graph
    coloring : dict
        Mapping (u, v) -> color, from the output of the solver
    layout : dict (optional)
        Precomputed layout positions {node: (x,y)}.
        If None, uses spring_layout.
    node_size : int
    width : float
        Edge width.
    """

    if layout is None:
        layout = nx.spring_layout(G, seed=1)

    # Convert colors to something matplotlib accepts
    # If colors are strings like "red" or "blue" this works automatically.
    # If they are integers, convert them to a matplotlib colormap.
    edge_colors = []

    # Determine if colors are numeric
    vals = list(coloring.values())
    numeric = all(isinstance(c, (int, float)) for c in vals)

    if numeric:
        # Map integers to a colormap (tab10 will give distinct colors)
        # You can switch to any discrete colormap you prefer.
        cmap = plt.cm.tab10
        unique_vals = sorted(set(vals))
        color_map = {c: cmap(i % 10) for i, c in enumerate(unique_vals)}
        edge_colors = [color_map[coloring[e]] for e in G.edges()]
    else:
        # Assume strings or valid matplotlib colors
        edge_colors = [coloring[e] for e in G.edges()]

    # Draw nodes
    nx.draw_networkx_nodes(G, layout, node_size=node_size, node_color="lightgray", edgecolors="black")

    # Draw edges
    nx.draw_networkx_edges(G, layout, width=width, edge_color=edge_colors)

    # Draw labels
    nx.draw_networkx_labels(G, layout, font_size=12)

    plt.axis("off")


def draw_all_edge_colorings(G, solutions, node_size=600, width=3, layout=None):
    """
    Draw all edge-colorings in the list `solutions` using matplotlib subplots.

    Parameters
    ----------
    G : networkx.Graph
        The underlying graph.
    solutions : list of dict
        Each element is a mapping (u, v) -> color, as returned by
        all_edge_colorings_with_vertex_constraints.
    node_size : int
        Node size for drawing.
    width : float
        Edge thickness.
    layout : dict or None
        Optional fixed layout dictionary {node: (x, y)}.
        If None, spring_layout is used once and reused for all subplots.

    Notes
    -----
    Colors may be:
        • strings (e.g., "red", "blue")
        • integers (mapped to a tab10 colormap)
    """

    if not solutions:
        print("No solutions to draw.")
        return

    if len(solutions) == 1:
        # Delegate to the single-solution helper, passing arguments along
        draw_edge_coloring(G, solutions[0], node_size=node_size, width=width, layout=layout)
        return

    # Use a consistent layout across all drawings.
    if layout is None:
        layout = nx.spring_layout(G, seed=1)

    n = len(solutions)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = axes.flatten()

    for ax_index, (solution, ax) in enumerate(zip(solutions, axes)):
        plt.sca(ax)
        ax.set_title(f"Solution {ax_index}", fontsize=12)

        # Determine whether colors are numeric
        vals = list(solution.values())
        numeric = all(isinstance(c, (int, float)) for c in vals)

        if numeric:
            cmap = plt.cm.tab10
            unique_vals = sorted(set(vals))
            color_map = {c: cmap(i % 10) for i, c in enumerate(unique_vals)}
            edge_colors = [color_map[solution[e]] for e in G.edges()]
        else:
            # assume matplotlib-friendly strings
            edge_colors = [solution[e] for e in G.edges()]

        nx.draw_networkx_nodes(G, layout, node_size=node_size,
                               node_color="lightgray", edgecolors="black")
        nx.draw_networkx_edges(G, layout, width=width, edge_color=edge_colors)
        nx.draw_networkx_labels(G, layout)

        ax.axis("off")

    # Clear extra axes
    for ax in axes[len(solutions):]:
        ax.axis("off")

    plt.tight_layout()

def read_graph_json(path):
    """
    Read a graph and per-vertex color constraints from a JSON file, with optional layout.

    JSON structure:
        {
          "vertices": {
            "v1": ["colorA", "colorB"],
            "v2": ["colorC", "colorD"]
          },

          "edges": [
            ["v1", "v2"],
            ["v2", "v3"]
          ],

          "layout": {
            "v1": [x, y],
            "v2": [x, y]
          }
        }

    The "layout" field is optional.  If present, it must map each vertex to
    a 2-element coordinate list; if missing, the function returns layout=None.

    Returns
    -------
    G : networkx.Graph
    vertex_colors : dict
    layout : dict or None
    """

    import json
    import networkx as nx

    with open(path) as f:
        data = json.load(f)

    # Required sections
    vertex_colors = data["vertices"]
    edges = data["edges"]

    # Build the graph
    G = nx.Graph()
    G.add_nodes_from(vertex_colors.keys())

    for edge in edges:
        if len(edge) != 2:
            raise ValueError(f"Invalid edge entry (must have 2 items): {edge}")
        u, v = edge
        G.add_edge(u, v)

    # Optional layout
    layout = None
    if "layout" in data:
        layout = {node: tuple(coords) for node, coords in data["layout"].items()}

    return G, vertex_colors, layout

class EdgeColoringInstance:
    """
    Container for a graph edge-coloring instance:
      - an undirected graph G
      - per-vertex color constraints
      - an optional layout for drawing

    Provides helpers to solve and draw solutions.
    """

    def __init__(self, G, vertex_colors, layout=None):
        self.G = G
        self.vertex_colors = vertex_colors
        self.layout = layout  # may be None

    @classmethod
    def from_json(cls, path, layout=None):
        """
        Create an instance from a JSON file.

        Parameters
        ----------
        path : str or Path
            JSON file path.
        layout : dict, optional
            Explicit layout {node: (x, y)} to override any layout in JSON.
        """
        G, vertex_colors, layout_dict = read_graph_json(path)
        return cls(G, vertex_colors, layout_dict)

    def solve(self):
        """Return all valid edge colorings satisfying the vertex constraints."""
        return all_edge_colorings_with_vertex_constraints(self.G, self.vertex_colors)

    def draw_coloring(self, solution, **kwargs):
        """
        Draw a single solution using the stored layout (if any).

        Extra kwargs are passed to draw_edge_coloring, e.g.
        node_size=..., width=...
        """
        draw_edge_coloring(self.G, solution, layout=self.layout, **kwargs)

    def draw_colorings(self, solutions=None, **kwargs):
        """
        Draw all solutions (or a given list) in a grid, using stored layout.

        Extra kwargs are passed to draw_all_edge_colorings.
        """
        if solutions is None:
            solutions = self.solve()
        draw_all_edge_colorings(self.G, solutions, layout=self.layout, **kwargs)


def is_colortrade(s1,s2):
    """Check if two colorings have any edges the same color.
    Return True if all edges are different colors, so this is a color trade.
    False if they share any edge color.
    """
    for edge, color in s1.items():
        if s2[edge] == color:
            return False
    return True

def build_trade_graph(sols):
    """Build a graph showing which solutions are color-trades"""
    G = nx.Graph()
    n = len(sols)
    G.add_nodes_from(range(n))
    
    for i, j in combinations(range(n), 2):
        if is_colortrade(sols[i], sols[j]):
            G.add_edge(i, j)
            
    return G
    
if __name__ == "__main__":
    # create explicitly
    hexagon = EdgeColoringInstance(nx.cycle_graph(6),
                                  {0: ['red', 'blue'],
                                   1: ['red', 'blue'],
                                   2: ['red', 'blue'],
                                   3: ['red', 'blue'],
                                   4: ['red', 'blue'],
                                   5: ['red', 'blue']})
    
    sols = hexagon.solve()
    print(f"Hexagon: found {len(sols)} colorings:")
    for sol in sols:
        print(sol)
        
    plt.figure(num="Hexagon coloring 0")
    hexagon.draw_coloring(sols[0])
    plt.show(block=False)
    
    plt.figure(num="Hexagon coloring 1")
    hexagon.draw_coloring(sols[1])
    plt.show(block=False)
    
    # Read from file
    square = EdgeColoringInstance.from_json("graphs/square.json")
    sols = square.solve()
    
    print(f"Square: found {len(sols)} colorings:")
    for sol in sols:
        print(sol)

    square.draw_colorings(sols)
    plt.gcf().canvas.manager.set_window_title("All colorings of the square")
    plt.show(block=False)

    # Compute color trade graph
    k4 = EdgeColoringInstance.from_json("graphs/k4.json")
    sols = k4.solve()
    
    k4.draw_colorings(sols)
    plt.gcf().canvas.manager.set_window_title("All 4-colorings of K4")
    plt.show(block=False)
    
    G = build_trade_graph(sols)
    plt.figure(num="Color trade graph for K4")
    nx.draw(G, with_labels=True)
    plt.show()
