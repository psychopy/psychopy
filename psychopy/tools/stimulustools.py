"""
Tools for interacting with various stimuli.

For example, lists of styles for Form/Slider, so that these static values
can be quickly imported from here rather than importing `psychopy.visual` (which is slow)
"""

formStyles = {
    'light': {
        'fillColor': [0.89, 0.89, 0.89],
        'borderColor': None,
        'itemColor': 'black',
        'responseColor': 'black',
        'markerColor': [0.89, -0.35, -0.28],
        'font': "Open Sans",
    },
    'dark': {
        'fillColor': [-0.19, -0.19, -0.14],
        'borderColor': None,
        'itemColor': 'white',
        'responseColor': 'white',
        'markerColor': [0.89, -0.35, -0.28],
        'font': "Open Sans",
    },
}

sliderStyles = ['slider', 'rating', 'radio', 'scrollbar', 'choice']
sliderStyleTweaks = ['labels45', 'triangleMarker']
