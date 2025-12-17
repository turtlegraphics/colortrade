"""
Look for Braille in k6
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

def cell_to_letter(sub: Sequence[Sequence[bool]]) -> Optional[str]:
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

class BitGrid():
    def __init__(self, bits):
        self.bits = bits

    def __str__(self):
        out = ''
        for r in self.bits:
            for c in r:
                out += '*' if c else '.'
            out += '\n'
        return out

    def to_Braille(self):
        count = 0
        out = ''
        for r in [0,3]:
            for c in [0,2,4]:
                subgrid = [lines[c:c+2] for lines in self.bits[r:r+3]]
                letter = cell_to_letter(subgrid)
                if letter is None:
                    letter = '.'
                else:
                    count += 1
                out += letter
        return out, count
                
class K6LatinSquare():
    def __init__(self, coloring):
        self.grid = [[None]*6 for i in range(6)]
        for (x,y),color in coloring.items():
            x = int(x)
            y = int(y)
            self.grid[x][y] = color
            self.grid[y][x] = color
        
        self.colors = set(coloring.values())
        for i in range(6):
            # fill the diagonal with the missing color from the row
            [self.grid[i][i]] = self.colors.difference(set(self.grid[i]))

    def to_binary(self, on_colors): 
        """Convert from a grid of colors to a binary grid,
        with 1 for the on_colors and 0 otherwise."""
        assert(set(on_colors).issubset(self.colors))
        return BitGrid([[(1 if c in on_colors else 0) for c in r] for r in self.grid])

    def __str__(self):
        out = ''
        for r in self.grid:
            for c in r:
                out += c[0:3] + ' '
            out += '\n'
        return out
    
k6 = ct.EdgeColoringInstance.from_json("graphs/k6.json")
sols = k6.solve()

#print(cell_to_letter([[1,1],[0,1],[1,0]]))

full_braille = collections.defaultdict(set)
half_braille = collections.defaultdict(set)
six_braille = collections.defaultdict(set)

for col_no, coloring in enumerate(sols):
    tops = set()
    bottoms = set()
    letters = [set() for x in range(6)]
    
    g = K6LatinSquare(coloring)
    for numcolors in range(7):
        for c_on in itertools.combinations(g.colors,numcolors):
            bits = g.to_binary(c_on)
            result, count = bits.to_Braille()
            if count == 6:
                full_braille[result].add((col_no,c_on))
            if result[0:3].find('.') == -1:
                tops.add(result[0:3])
            if result[3:6].find('.') == -1:
                bottoms.add(result[3:6])

            for i,c in enumerate(result):
                if c != '.':
                    letters[i].add(c)
                    
    for t in tops:
        for b in bottoms:
            half_braille[t + b].add(col_no)

    all_letters = [''.join(sorted(list(letters[x]))) for x in range(6)]
    if '' in all_letters:
        print(col_no,'failed entirely') # never happens!
    else:
        six_braille['-'.join(all_letters)].add(col_no)
    
print('='*80)
print('Possible solutions using one set of colors in all six cells')
print('='*80)

for k in full_braille:
    for (i,c_on) in full_braille[k]:
        print(i,end=',')
    print()
    print(k)

print()
print('='*80)
print('Possible solutions using one set of colors for the top row, and a second set for the bottom row')
print('='*80)
for k in sorted(list(half_braille)):
    print(k)
#    print('using coloring numbers:')
#    for i in half_braille[k]:
#        print(i,end=',')
#    print()

    
# Let's get some words!
dfile = "words-with-6-letters.txt"
dictionary = [x.strip() for x in open(dfile).readlines()]

good_words = ['iguana','option','ethnic','gunman','sonata','zinnia','erotic','grotto','geneva','seneca','zydeco']

print()
print('='*80)
print('Using different colorings for each 2x3 cell:')
print('all possible letters in each cell and words made from those')
print('='*80)

possible_solutions = set()
for k in six_braille:
    print()
    print(k)
    for i in six_braille[k]:
        print(i,end=',')
    print()
    spots = k.split('-')
    for w in dictionary:
        good = True
        for i,c in enumerate(w):
            if c not in spots[i]:
                good = False
                break
        if good:
            print(w)
            possible_solutions.add(w)

    
def colors(square, word):
    """Iterator through the color lists needed to match the six letter word"""
    for i in range(6):
        for numcolors in range(7):
            for c_on in itertools.combinations(g.colors,numcolors):
                bits = square.to_binary(c_on)
                result, count = bits.to_Braille()
                if result[i] == word[i]:
                    yield((i,c_on))

def mincolors(square,word):
    best = {}
    for (i,c_on) in colors(square,word):
        if i not in best:
            best[i] = c_on
        else:
            if len(c_on) < len(best[i]):
                best[i] = c_on
    return best

def is_two_colors(square, word):
    bestcolors = mincolors(square,word)
    if len(bestcolors) < 6:
        return False
    if max([len(bestcolors[spot]) for spot in bestcolors]) > 2:
        return False
    return True

def has_one_color_on(square, word):
    """Test if a word can be done including a single always-on color."""
    works = {}
    for c in square.colors:
        works[c] = [False]*6

    for (i,col_on) in colors(square,word):
        for c in square.colors:
            if c in col_on:
                works[c][i] = True

    result = []
    for c in square.colors:
        if all(works[c]):
            result.append(c)

    return result

print()
print('='*80)
print('Which colorings to use for each word solution')
print('including: if there is a color that is ON for all six cells')
print('and if the word can be realized with only two colors per cell')
print('='*80)

#for (i,col_on) in colors(K6LatinSquare(sols[129]),"geneva"):
#    print(i,col_on)

for word in sorted(list(possible_solutions)):
    print(word)
    this_word_sols = []
    for i,coloring in enumerate(sols):
        square = K6LatinSquare(coloring)
        if len(mincolors(square,word)) == 6:
            this_word_sols.append(i)
            if is_two_colors(square, word):
                print('  on solution',i,'can be done with two colors per cell')
            clist = has_one_color_on(square, word)
            if clist:
                print('  on solution',i,'has full color on:',clist)
    print('   all sols:', ', '.join([str(j) for j in this_word_sols]))

print()
print()
print('='*80)
print('Possible color usage, per cell, for selected words')
print('='*80)

puzzle_words = ['seneca','grotto','gunman','option']
for word in puzzle_words:
    print()
    print('-'*10,word,'-'*10)
    for i,coloring in enumerate(sols):
        square = K6LatinSquare(coloring)
        if len(mincolors(square,word)) == 6:
            print('COLORING',i)
            for (spot, col_on) in colors(square,word):
                print(spot,col_on)
