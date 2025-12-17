#
# support code for the warmup puzzle
#
import sys
import colortrade_tools as ct
import random
import re

if len(sys.argv) == 1:
    printing_solution = False
elif sys.argv[1] == '-solution':
    printing_solution = True
else:
    print('usage: warmup [-solution]', file=sys.stderr)
    sys.exit(1)
        
answer = "LOSANGELES"
#
# Code: # = draw colored edge, no letter
#       ? = draw next letter of solution word
#       . = draw random letter
#         = draw no letter
#     1-6 = force color on this edge

graphs = [
    # (filename, c1, c2, codes, scale)
    #    ('cube', 0, 1, '############', 1),  # example graph
    ('wheel6', 1, 0, '...?###...?#', 1.3),
    ('square', 0, 1 , '#?#?', 1.3),
    ('triangle', 0, 0, '.6.', 1.0),
    ('thetasub', 1, 0, '#?#?.#', 1.0),
    ('k4', 0, 3, '#.??..', 2.2),
    ('pinwheel6', 0, 0, '......', 0.7),
    ('hexagon', 0, 1, '#?#?# ', 1),
    ('bowtie', 0, 0, '....  ', 1.4)
    ]

random.seed(25)

colornames = ['orange','yellow','green','blue','purple','black']

frequencies = {
    'E': 12.10, 'T': 8.94, 'A': 8.55, 'O': 7.47, 'I': 7.33, 'N': 7.17,
    'S': 6.73, 'R': 6.33, 'H': 4.96, 'L': 4.21, 'D': 3.87, 'C': 3.16,
    'U': 2.68, 'M': 2.53, 'W': 2.34, 'F': 2.18, 'G': 2.09, 'Y': 2.04,
    'P': 1.66, 'B': 1.60, 'V': 1.06, 'K': 0.87, 'J': 0.23, 'X': 0.20,
    'Q': 0.09, 'Z': 0.06
}

def get_random_letter_by_frequency():
    """
    Selects a single random letter based on English frequency weights.
    Returns a single-character string (uppercase).
    """
    # random.choices returns a list, so we take the first element
    return random.choices(list(frequencies.keys()), weights=list(frequencies.values()), k=1)[0]

def texit(g, c1, c2, letters, scale):
    global solutionletter
    
    original = g.draw_latex(c1,scale=scale)
    blanked = g.draw_latex(c2,scale=scale)

    # substitute color names
    for i,color in enumerate(colornames):
        original = original.replace(color,f'color{i+1}')
        blanked = blanked.replace(color,f'color{i+1}')

    # remove node labels
    original = re.sub(r'{.};',r'{};',original)
    blanked = re.sub(r'{.};',r'{};',blanked)
    
    # Now handle the blanked out graph
    result = ''
    edge = 0
    for line in blanked.split('\n'):
        if line.find('draw') == -1:
            result += line + '\n'
            continue
        else:
            # extract information from draw line
            # \draw[CTedge, color1] (v0) -- (v1);
            pattern = r"(\w+)]"
            color = re.search(pattern, line).group(1)
            pattern = r"\((\w+)\) -- \((\w+)\)"
            v0,v1 = re.search(pattern, line).groups()

            c = letters[edge]
            if c == '#':
                out = line
            elif c in '123456':
                out = re.sub('color.','color'+c, line)
            else:
                v = c
                if c == '?':
                    v = answer[solutionletter]
                    solutionletter += 1
                if c == '.':
                    v = get_random_letter_by_frequency()
                nodestyle = 'letter'
                if printing_solution and c == '?':
                    nodestyle = 'answer'
                out = f'  \\path ({v0}) -- node[{nodestyle}, midway]{{{v}}} ({v1});'
                
            if printing_solution and c1 != c2:
                result += line
            
            result += out + '\n'
            edge += 1

    return(original, result)

solutionletter = 0

for fname, coloring1, coloring2, letters, scale in graphs:
    g = ct.EdgeColoringInstance.from_json(f'graphs/{fname}.json')
    sols = g.solve()
    original, blanked = texit(g, sols[coloring1], sols[coloring2],letters,scale)
    print(f'%\n% {fname}\n%')
    print(r'\startctgraph')
    print(original)
    print(r'\scramble')
    print(blanked)
    
