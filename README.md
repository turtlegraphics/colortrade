# colortrade

Code for working with color trades on graphs. See John Carr's thesis work for definitions:

https://etd.auburn.edu/bitstream/handle/10415/8398/Carr_Dissertation.pdf?sequence=2

The file `colortrade_tools.py` is a collection of utility functions.

The program `colorings.py` will show you all colorings of a specified graph,
calculate the associated color trade graph, and show that along with some statistics on it.

Graphs and their vertex color lists are specified by JSON, see examples in the graphs folder.

Use it like so:

    python colorings.py graphs/k4.json -showall
    



