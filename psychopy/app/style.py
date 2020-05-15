# Create library of "on brand" colours
cLib = {
    'none': [127, 127, 127, 0],
    'black': [0, 0, 0],
    'grey': [102, 102, 110],
    'white': [242, 242, 242],
    'red': [242, 84, 91],
    'green': [138, 234, 146],
    'blue': [2, 169, 234],
    'yellow': [241, 211, 2],
    'orange': [236, 151, 3],
    'purple': [195, 190, 247],
    'darker': {},
    'lighter': {},
    'very': {'lighter': {},
             'darker': {}}
}
# Create light and dark variants of each colour by +-15 to each value
for c in cLib:
     if not c in ['darker', 'lighter', 'none', 'very']:
         cLib['darker'][c] = [max(0, n-15) for n in cLib[c]]
         cLib['lighter'][c] = [min(255, n+15) for n in cLib[c]]
# Create very light and very dark variants of each colour by a further +-30 to each value
for c in cLib['lighter']:
    cLib['very']['lighter'][c] = [min(0, n+30) for n in cLib['lighter'][c]]
for c in cLib['darker']:
    cLib['very']['darker'][c] = [max(0, n-30) for n in cLib['darker'][c]]

# Create light and dark colour schemes
cs = {
    'Light': {

    },
    'Dark': {

    }
}
