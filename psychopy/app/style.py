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
    cLib['very']['lighter'][c] = [min(255, n+30) for n in cLib['lighter'][c]]
for c in cLib['darker']:
    cLib['very']['darker'][c] = [max(0, n-30) for n in cLib['darker'][c]]

# Create light and dark colour schemes
cs_light = {
    # Toolbar
    'toolbar_bg': cLib['darker']['white'],
    'tool_hover': cLib['very']['darker']['white'],
    # Frame
    'frame_bg': cLib['darker']['white'],
    'grippers': cLib['darker']['white'],
    'note_bg': cLib['white'],
    'tab_face': cLib['white'],
    'tab_active': cLib['lighter']['white'],
    'tab_txt': cLib['lighter']['black'],
    'docker_face': cLib['very']['darker']['white'],
    'docker_txt': cLib['black'],
    ## Builder
    # Routine canvas
    'rtcanvas_bg': cLib['lighter']['white'],
    'time_grid': cLib['very']['darker']['white'],
    'time_txt': cLib['black'],
    'rtcomp_txt': cLib['black'],
    'rtcomp_bar': cLib['red'],
    'rtcomp_distxt': cLib['very']['darker']['white'],
    'rtcomp_disbar': cLib['very']['darker']['white'],
    'isi_bar': cLib['red'] + [75],
    'isi_txt': cLib['lighter']['white'],
    'isi_disbar': cLib['grey'] + [75],
    'isi_distxt': cLib['lighter']['white'],
    # Component panel
    'cpanel_bg': cLib['white'],
    'cbutton_hover': cLib['darker']['white'],
    'catbutton_bg': cLib['white'],
    'catbutton_hover': cLib['blue'],
    'catbutton_txt': cLib['black'],
    # Flow panel
    'fpanel_bg': cLib['darker']['white'],
    'fpanel_ln': cLib['very']['lighter']['grey'],
    'frt_slip': cLib['red'],
    'frt_nonslip': cLib['blue'],
    'frt_txt': cLib['lighter']['white'],
    'loop_face': cLib['grey'],
    'loop_txt': cLib['lighter']['white'],
    'fbtns_face': cLib['darker']['white'],
    'fbtns_hover': cLib['white'],
    'fbtns_txt': cLib['black']
    ## Coder
    }
cs_dark = {
    # Toolbar
    'toolbar_bg': cLib['darker']['grey'],
    'tool_hover': ['grey'],
    # Frame
    'frame_bg': cLib['darker']['grey'],
    'grippers': cLib['darker']['grey'],
    'note_bg': cLib['grey'],
    'tab_face': cLib['darker']['grey'],
    'tab_active': cLib['lighter']['grey'],
    'tab_txt': cLib['lighter']['white'],
    'docker_face': cLib['very']['darker']['grey'],
    'docker_txt': cLib['white'],
    ## Builder
    # Routine canvas
    'rtcanvas_bg': cLib['lighter']['grey'],
    'time_grid': cLib['very']['lighter']['grey'],
    'time_txt': cLib['darker']['white'],
    'rtcomp_txt': cLib['white'],
    'rtcomp_bar': cLib['red'],
    'rtcomp_distxt': cLib['grey'],
    'rtcomp_disbar': cLib['grey'],
    'isi_bar': cLib['red'] + [75],
    'isi_txt': cLib['lighter']['white'],
    'isi_disbar': cLib['grey'] + [75],
    'isi_distxt': cLib['lighter']['white'],
    # Component panel
    'cpanel_bg': cLib['grey'],
    'cbutton_hover': cLib['lighter']['grey'],
    'catbutton_bg': cLib['grey'],
    'catbutton_hover': cLib['blue'],
    'catbutton_txt': cLib['white'],
    # Flow panel
    'fpanel_bg': cLib['darker']['grey'],
    'fpanel_ln': cLib['lighter']['grey'],
    'frt_slip': cLib['red'],
    'frt_nonslip': cLib['blue'],
    'frt_txt': cLib['lighter']['white'],
    'loop_face': cLib['darker']['white'],
    'loop_txt': cLib['lighter']['white'],
    'fbtns_face': cLib['darker']['grey'],
    'fbtns_hover': cLib['grey'],
    'fbtns_txt': cLib['white']
    }