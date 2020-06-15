import psychopy

# Create library of "on brand" colours
cLib = {
    'none': [127, 127, 127, 0],
    'black': [0, 0, 0],
    'grey': [102, 102, 110],
    'white': [242, 242, 242],
    'red': [242, 84, 91],
    'green': [108, 204, 116],
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
    'txt_default': cLib['black'],
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
    # Plate Buttons
    'platebtn_bg': cLib['white'],
    'platebtn_txt': cLib['black'],
    'platebtn_hover': cLib['red'],
    'platebtn_hovertxt': cLib['white'],
    ## Builder
    # Routine canvas
    'rtcanvas_bg': cLib['lighter']['white'],
    'time_grid': cLib['very']['darker']['white'],
    'time_txt': cLib['grey'],
    'rtcomp_txt': cLib['black'],
    'rtcomp_bar': cLib['blue'],
    'rtcomp_force': cLib['orange'],
    'rtcomp_distxt': cLib['very']['darker']['white'],
    'rtcomp_disbar': cLib['very']['darker']['white'],
    'isi_bar': cLib['red'] + [75],
    'isi_txt': cLib['lighter']['white'],
    'isi_disbar': cLib['grey'] + [75],
    'isi_distxt': cLib['lighter']['white'],
    # Component panel
    'cpanel_bg': cLib['white'],
    'cbutton_hover': cLib['darker']['white'],
    # Flow panel
    'fpanel_bg': cLib['white'],
    'fpanel_ln': cLib['very']['lighter']['grey'],
    'frt_slip': cLib['blue'],
    'frt_nonslip': cLib['green'],
    'frt_txt': cLib['lighter']['white'],
    'loop_face': cLib['grey'],
    'loop_txt': cLib['lighter']['white'],
    'fbtns_face': cLib['darker']['white'],
    'fbtns_txt': cLib['black'],
    ## Coder
    # Source Assistant
    'src_bg': cLib['white'],
    # Source Assistant: Structure
    'struct_bg': cLib['white'],
    'struct_txt': cLib['black'],
    'struct_hover': cLib['red'],
    'struct_hovertxt': cLib['white'],
    # Source Assistant: File Browser
    'brws_bg': cLib['white'],
    'brws_txt': cLib['black'],
    'brws_hover': cLib['red'],
    'brws_hovertxt': cLib['white']
    # Shell
    }
cs_dark = {
    'txt_default': cLib['white'],
    # Toolbar
    'toolbar_bg': cLib['darker']['grey'],
    'tool_hover': ['grey'],
    # Frame
    'frame_bg': cLib['darker']['grey'],
    'grippers': cLib['darker']['grey'],
    'note_bg': cLib['grey'],
    'tab_face': cLib['grey'],
    'tab_active': cLib['lighter']['grey'],
    'tab_txt': cLib['lighter']['white'],
    'docker_face': cLib['very']['darker']['grey'],
    'docker_txt': cLib['white'],
    # Plate Buttons
    'platebtn_bg': cLib['grey'],
    'platebtn_txt': cLib['white'],
    'platebtn_hover': cLib['red'],
    'platebtn_hovertxt': cLib['white'],
    ## Builder
    # Routine canvas
    'rtcanvas_bg': cLib['lighter']['grey'],
    'time_grid': cLib['very']['lighter']['grey'],
    'time_txt': cLib['darker']['white'],
    'rtcomp_txt': cLib['white'],
    'rtcomp_bar': cLib['blue'],
    'rtcomp_force': cLib['orange'],
    'rtcomp_distxt': cLib['grey'],
    'rtcomp_disbar': cLib['grey'],
    'isi_bar': cLib['red'] + [75],
    'isi_txt': cLib['lighter']['white'],
    'isi_disbar': cLib['grey'] + [75],
    'isi_distxt': cLib['lighter']['white'],
    # Component panel
    'cpanel_bg': cLib['grey'],
    'cbutton_hover': cLib['lighter']['grey'],
    # Flow panel
    'fpanel_bg': cLib['darker']['grey'],
    'fpanel_ln': cLib['lighter']['grey'],
    'frt_slip': cLib['blue'],
    'frt_nonslip': cLib['green'],
    'frt_txt': cLib['lighter']['white'],
    'loop_face': cLib['darker']['white'],
    'loop_txt': cLib['black'],
    'fbtns_face': cLib['grey'],
    'fbtns_txt': cLib['white'],
    ## Coder
    # Source Assistant
    'src_bg': cLib['grey'],
    # Source Assistant: Structure
    'struct_txt': cLib['white'],
    'struct_hover': cLib['red'],
    'struct_hovertxt': cLib['white'],
    # Source Assistant: File Browser
    'brws_txt': cLib['white'],
    'brws_hover': cLib['red'],
    'brws_hovertxt': cLib['white']
    # Shell
    }
if psychopy.prefs.app['darkmode']:
    cs = cs_dark
else:
    cs = cs_light
