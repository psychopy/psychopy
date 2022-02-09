import pytest
from psychopy.visual import Window
from psychopy.visual.windowframepack import ProjectorFramePacker

"""define ProjectorFramePack configurations, test the logic

    test:
    cd psychopy/psychopy/
    py.test -k projectorframepack --cov-report term-missing --cov visual/windowframepack.py
"""


class Test_class_ProjectorFramePacker():
    """
    """
    def setup_class(self):
        self.win = Window(monitor='LightCrafter4500', screen=2, fullscr=True, color='gray', useFBO = True)
        self.win.setRecordFrameIntervals()
        self.packer = ProjectorFramePacker (self.win)

    def teardown_class(self):
        self.win.close()

    def flip (self, frames=120):
        for i in range(frames):
            self.win.flip()

if __name__ == '__main__':
    cls = Test_class_ProjectorFramePacker()
    cls.setup_class()
    originalFPS = cls.win.fps()
    print('originalFPS = ' + str(originalFPS))
    cls.flip(3)
    assert (cls.win.frames == 3)
    assert (cls.packer.flipCounter == 3)
    cls.flip(33)
    assert (cls.win.frames == 36)
    assert (cls.packer.flipCounter == 36)
    finalFPS = cls.win.fps()
    print('finalFPS = ' + str(finalFPS))
    cls.teardown_class()
