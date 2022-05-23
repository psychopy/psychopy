from pathlib import Path

import pytest
import tempfile
from psychopy import visual, hardware, event
import time

@pytest.mark.skip_under_vm
class TestWebcam:
    """
    Tests for the hardware.Webcam class, cannot be run online as there is no webcam to read from.
    """

    def setup(self):
        # Make window
        self.win = visual.Window()
        # Make webcam object
        self.obj = hardware.Webcam(self.win, name="testWebcam")
        # Make textbox to display instructiosn in
        self.instr = visual.TextBox2(
            self.win, "",
            pos=(0, -1), anchor="bottom center", alignment="bottom center", size=(2, 0.5), units="norm"
        )
        # Initialise webcam
        self.obj.initialize()

    def _record(self, dur):
        # Start recording
        self.obj.start()
        # Update instructions
        self.instr.text = "Webcam is recording..."
        self.instr.draw()
        self.win.flip()
        # Wait
        time.sleep(dur)
        # Stop recording
        self.obj.stop()

    def testLiveImage(self):
        """
        Webcam footage should be able to be displayed live by passing Webcam.lastFrame to an ImageStim each frame.

        There should be syntactic sugar such which means passing a Webcam object to image stim should set the image
        as Webcam.lastFrame each time the ImageStim is drawn.
        """
        # Make image stim to show frames in
        img = visual.ImageStim(
            self.win,
            pos=(0, -0.5), anchor="bottom center", units="norm"
        )
        # Set instructions
        self.instr.text = "You should be seeing live footage from your webcam. Press ENTER if so, ESC if not."
        # Try with and without syntactic sugar
        for withSugar in (True, False):
            # Start recording webcam
            self.obj.start()
            # Set image as webcam obj if using sugar
            if withSugar:
                img.image = self.obj
            # Display live footage until user presses ESC or ENTER
            resp = []
            while not resp:
                # Update keys
                resp = event.getKeys(['escape', 'enter'])
                if not withSugar:
                    # Set image as last frame of webcam (if using sugar, this should be handled by Image.draw)
                    img.image = self.obj.lastFrame
                # Draw
                img.draw()
                self.instr.draw()
                self.win.flip()
            # Stop recording
            self.obj.stop()
            # Check that user confirmed working
            assert "enter" in resp

    def testAfterMovie(self):
        """
        Should be able to get last clip from Webcam object and supply it directly to a MovieStim
        """
        # Create movie stim
        mov = visual.MovieStim(
            self.win,
            pos=(0, -0.5), anchor="bottom center", units="norm"
        )
        # Record for 5s
        self._record(5)
        # Set movie stim as last clip
        mov.setMovie(self.obj.lastClip)
        # Set instructions
        self.instr.text = "You should be seeing the 5s recording from just now. Press ENTER if so, ESC if not."
        # Play
        resp = []
        while not resp:
            # Update keys
            resp = event.getKeys(['escape', 'enter'])
            # Draw
            mov.draw()
            self.instr.draw()
            self.win.flip()
        # Check that user confirmed working
        assert "enter" in resp

    def testLiveMovie(self):
        """
        Should be able to supply a MovieStim with a Webcam object and have the MovieStim show the content from the
        Webcam as it is recorded.
        """
        # Create movie stim
        mov = visual.MovieStim(
            self.win,
            pos=(0, -0.5), anchor="bottom center", units="norm"
        )
        # Set movie stim as last clip
        mov.setMovie(self.obj)
        # Set instructions
        self.instr.text = "You should be seeing live footage from your webcam. Press ENTER if so, ESC if not."
        # Play
        resp = []
        while not resp:
            # Update keys
            resp = event.getKeys(['escape', 'enter'])
            # Draw
            mov.draw()
            self.instr.draw()
            self.win.flip()
        # Check that user confirmed working
        assert "enter" in resp

    def testSaving(self):
        # Record for 5s
        self._record(5)
        # Save to temp file
        filename = Path(tempfile.tempdir) / "testWebcamRecording.mp4"
        self.obj.save(filename)
        # Make MovieStim to display recording
        mov = visual.MovieStim(
            self.win,
            pos=(0, -0.5), anchor="bottom center", units="norm"
        )
        mov.setMovie(filename)
        # Set instructions
        self.instr.text = "You should be seeing the 5s recording from just now. Press ENTER if so, ESC if not."
        # Play
        resp = []
        while not resp:
            # Update keys
            resp = event.getKeys(['escape', 'enter'])
            # Draw
            mov.draw()
            self.instr.draw()
            self.win.flip()
        # Check that user confirmed working
        assert "enter" in resp
