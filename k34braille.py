"""
Look for Braille in k3,4
"""

from __future__ import annotations
from typing import List, Optional, Sequence, Tuple
import collections
import itertools
import colortrade_tools as ct

# Standard (uncontracted) Braille: dots 1–6 map to a 2x3 cell like:
#   (row, col): dot#
#   (0,0)=1  (0,1)=4
#   (1,0)=2  (1,1)=5
#   (2,0)=3  (2,1)=6
DOT_POS = {
    1: (0, 0), 2: (1, 0), 3: (2, 0),
    4: (0, 1), 5: (1, 1), 6: (2, 1),
}

# Letters a–z in standard English Braille (no contractions).
# Represent each letter by the set of raised dots {1..6}.
BRAILLE_LETTER_TO_DOTS = {
    "a": {1},
    "b": {1, 2},
    "c": {1, 4},
    "d": {1, 4, 5},
    "e": {1, 5},
    "f": {1, 2, 4},
    "g": {1, 2, 4, 5},
    "h": {1, 2, 5},
    "i": {2, 4},
    "j": {2, 4, 5},

    "k": {1, 3},
    "l": {1, 2, 3},
    "m": {1, 3, 4},
    "n": {1, 3, 4, 5},
    "o": {1, 3, 5},
    "p": {1, 2, 3, 4},
    "q": {1, 2, 3, 4, 5},
    "r": {1, 2, 3, 5},
    "s": {2, 3, 4},
    "t": {2, 3, 4, 5},

    "u": {1, 3, 6},
    "v": {1, 2, 3, 6},
    "w": {2, 4, 5, 6},
    "x": {1, 3, 4, 6},
    "y": {1, 3, 4, 5, 6},
    "z": {1, 3, 5, 6},
}

# Invert: dots -> letter
BRAILLE_DOTS_TO_LETTER = {frozenset(v): k for k, v in BRAILLE_LETTER_TO_DOTS.items()}


def _validate_4x3_bool_grid(grid: Sequence[Sequence[bool]]) -> None:
    if len(grid) != 3:
        raise ValueError(f"Expected 3 rows, got {len(grid)}")
    for r, row in enumerate(grid):
        if len(row) != 4:
            raise ValueError(f"Row {r} expected 4 columns, got {len(row)}")
        if not all(isinstance(x, (bool, int)) for x in row):
            raise TypeError("Grid entries must be booleans (or 0/1).")


def _subcell_to_letter(sub: Sequence[Sequence[bool]]) -> Optional[str]:
    """
    sub is a 3x2 boolean grid (rows 0..2, cols 0..1).
    Returns 'a'..'z' if it matches a standard Braille letter, else None.
    """
    # Compute raised dot set based on DOT_POS mapping.
    raised = set()
    for dot, (rr, cc) in DOT_POS.items():
        if bool(sub[rr][cc]):
            raised.add(dot)
    return BRAILLE_DOTS_TO_LETTER.get(frozenset(raised))


def braille_pair_from_4x3(grid: Sequence[Sequence[bool]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Input: 3 lists of 4 booleans (a 3x4 grid).
    Interprets it as two adjacent Braille cells (each 3x2),
    and returns (left_letter_or_None, right_letter_or_None).
    """
    _validate_4x3_bool_grid(grid)

    left = [row[0:2] for row in grid]   # 3x2
    right = [row[2:4] for row in grid]  # 3x2

    return _subcell_to_letter(left), _subcell_to_letter(right)

k34 = ct.EdgeColoringInstance.from_json("graphs/k34.json")
sols = k34.solve()
pairs = set()
OOlist = []
ZElist = []
for i,s in enumerate(sols):
    g = k34.get_bipartite_grid(s)

    for colors_on in range(5):
        for onset in itertools.combinations('bgor',colors_on):
            bit = collections.defaultdict(int)
            for c in onset:
                bit[c] = 1

            bitgrid = [[bit[c[0]] for c in r] for r in g]
            (llet,rlet) = braille_pair_from_4x3(bitgrid)
            if llet is not None and rlet is not None:
                print(f'solution {i}: {llet} {rlet} using {str(onset)}')
                pairs.add(llet + rlet)
                if llet + rlet == 'oo':
                    OOlist.append(i)
                if llet + rlet == 'ze':
                    ZElist.append(i)
    
for p in pairs:
    print(p,end=' ')
print()


print('OO grids')
for i in OOlist: # oo
    for j in range(len(sols)):
        if ct.is_colortrade(sols[i],sols[j]):
            print(i,'trades with',j)

print()
print('ZE grids')
for i in ZElist: # ze
    for j in range(len(sols)):
        if ct.is_colortrade(sols[i],sols[j]):
            print(i,'trades with',j)

print()
print('Solution 15')
print(k34.get_bipartite_grid(sols[15]))
print('Solution 17')
print(k34.get_bipartite_grid(sols[17]))

print('TIKZ graphs for use in the puzzle')
for x in [0,6,15,17]:
    tex = k34.draw_latex(sols[x], node_style = "gnode", edge_style = "gedge")
    print()
    print('% Coloring number',x)
    if x in [6,17]:
        print('%  with swapped colors')
        # swap orange and red
        tex = tex.replace('red','swap')
        tex = tex.replace('orange','red')
        tex = tex.replace('swap','orange')
    print(tex)
    
