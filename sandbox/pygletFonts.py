# -*- coding: latin-1 -*-
from pyglet import window, font, gl

win = window.Window()

alg = font.load('blah', 100, bold=False, dpi=72)#will be 24 pixels high?
alg2 = font.load('arial', 24, bold=True)
text = font.Text(alg, u'hello my friend i thought this to be okï', x=100, y = 100, #width=150, 
                 halign=font.Text.RIGHT, valign=font.Text.TOP)
text2 = font.Text(alg2, u'hello my friend i thought this\220 to be okï', x=100, y = 100, #width=150,
                 halign='left', valign='bottom')
text.text='hekk'
#gl.glRotatef(20,0.0,0.0,1.0)    
text.draw()

while not win.has_exit:
    win.dispatch_events()
    win.clear()
    text.draw()
    text2.draw()
    win.flip()
