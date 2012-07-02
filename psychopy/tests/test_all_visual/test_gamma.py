from psychopy import visual

def test_low_gamma():
    """setting gamma low (dark screen)"""
    win = visual.Window([600,600], gamma=0.5)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()
def test_mid_gamma():
    """setting gamma high (bright screen)"""
    win = visual.Window([600,600], gamma=2.0)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()
def test_high_gamma():
    """setting gamma high (bright screen)"""
    win = visual.Window([600,600], gamma=4.0)#should make the entire screen bright
    for n in range(5):
        win.flip()
    assert win.useNativeGamma==False
    win.close()
def test_no_gamma():
    """check that no gamma is used if not passed"""
    win = visual.Window([600,600])#should not change gamma
    assert win.useNativeGamma==True
    win.close()
    """Or if gamma is provided but by a default monitor?"""
    win = visual.Window([600,600], monitor='blaah')#should not change gamma
    assert win.useNativeGamma==True
    win.close()
    
if __name__=='__main__':
    test_high_gamma()
