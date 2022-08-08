import time
from numpy.random import choice as randchoice
import pandas as pd
import scipy.stats as sp

from psychopy.tests import skip_under_vm
from psychopy import colors
from psychopy.tools.attributetools import attributeSetter, logAttrib


pd.options.display.float_format = "{:,.0f}".format


@skip_under_vm
class TestAttributeSetterSpeed:
    nCalls = 1000

    class _Base:
        name = "test"
        autoLog = True

    def test_basic(self):
        class AttributeSetter(self._Base):
            @attributeSetter
            def test(self, value):
                self.__dict__['test'] = value

        class PropertySetter(self._Base):
            @property
            def test(self):
                return self._test

            @test.setter
            def test(self, value):
                self._test = value

        createTimes = {}
        setTimes = {}
        getTimes = {}

        for cls in (AttributeSetter, PropertySetter):
            # Setup timer
            createTimes[cls.__name__] = []
            setTimes[cls.__name__] = []
            getTimes[cls.__name__] = []

            last = time.time_ns()
            # Create loads of objects
            for n in range(self.nCalls):
                obj = cls()
                createTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
            # Set and read values loads of times on last object
            for val in range(self.nCalls):
                # Set value
                obj.test = val
                setTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
                # Get value
                gotCol = obj.test
                getTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()

        # Create total array
        totalTimes = pd.DataFrame(createTimes) + pd.DataFrame(setTimes) + pd.DataFrame(getTimes)

        # Print results
        print("\n")
        for key, times in {
            'creating objects': createTimes,
            'setting attribute': setTimes,
            'getting attribute': getTimes,
            'performing all operations': totalTimes,
        }.items():
            # Convert to dataframe using ms
            df = pd.DataFrame(times) / self.nCalls
            a = df['AttributeSetter']
            b = df['PropertySetter']
            # Calculate descriptives and do a T-test
            T, p = sp.ttest_ind(a, b)
            std = (a.std() + b.std()) / 2
            diff = a.mean() - b.mean()
            # If diff < 0, then attribute setter is faster
            if diff < 0:
                faster = "AttributeSetter"
                slower = "PropertySetter"
            else:
                faster = "PropertySetter"
                slower = "AttributeSetter"
            # Print any significant differences
            if p < 0.05:
                # Construct string to print
                out = (
                    f"{faster} WAS significantly faster than {slower} when {key} "
                    f"(diff: {abs(diff):.2f}ns, T: {T:.2f}, p: {p:.2f})"
                )
            else:
                # Construct string to print
                out = (
                    f"{faster} WAS NOT significantly faster than {slower} when {key}"
                )
            print(out)

    def test_color_attribs(self):
        class AttributeSetter(self._Base):
            def __init__(self, colorSpace):
                self.colorSpace = colorSpace

            @attributeSetter
            def colorSpace(self, value):
                self.__dict__['colorSpace'] = value
                if hasattr(self, "_color"):
                    self.__dict__['color'] = getattr(self._color, self.colorSpace)

            @attributeSetter
            def color(self, value):
                self._color = colors.Color(value, self.colorSpace)
                self.__dict__['color'] = getattr(self._color, self.colorSpace)

        class PropertySetter(self._Base):
            def __init__(self, colorSpace):
                self.colorSpace = colorSpace

            @property
            def color(self):
                if hasattr(self, "_color"):
                    return getattr(self._color, self.colorSpace)

            @color.setter
            def color(self, value):
                self._color = colors.Color(value, self.colorSpace)

        createTimes = {}
        firstTimes = {}
        spaceTimes = {}
        setTimes = {}
        getTimes = {}
        getSameTimes = {}

        for cls in (AttributeSetter, PropertySetter):
            # Setup timer
            createTimes[cls.__name__] = []
            firstTimes[cls.__name__] = []
            spaceTimes[cls.__name__] = []
            setTimes[cls.__name__] = []
            getTimes[cls.__name__] = []
            getSameTimes[cls.__name__] = []

            last = time.time_ns()
            # Create loads of objects
            for n in range(self.nCalls):
                obj = cls(randchoice(("hsv", "rgb", "rgb255")))
                createTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
                # Set initial values
                obj.color = "red"
                obj.colorSpace = randchoice(("hsv", "rgb", "rgb255"))
                gotVal = obj.color
                firstTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
            # Set and read values loads of times on last object
            for n in range(self.nCalls):
                # Set value
                obj.color = randchoice(("red", "green", "blue"))
                setTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
                # Set color space
                obj.colorSpace = randchoice(("hsv", "rgb", "rgb255"))
                spaceTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
                # Get value
                gotCol = obj.color
                getTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()
            # Get unchanged value repeatedly, but in different color space than it was set
            obj.colorSpace = "hsv"
            obj.color = "red"
            obj.colorSpace = "rgb1"
            last = time.time_ns()
            for n in range(self.nCalls):
                # Get value
                gotCol = obj.color
                getSameTimes[cls.__name__].append(time.time_ns() - last)
                last = time.time_ns()

        # Create total array
        totalTimes = pd.DataFrame(createTimes) + pd.DataFrame(firstTimes) + pd.DataFrame(spaceTimes) + pd.DataFrame(setTimes) + pd.DataFrame(getTimes) + pd.DataFrame(getSameTimes)

        # Print results
        print("\n")
        for key, times in {
            'creating objects': createTimes,
            'setting and getting color on a new object': firstTimes,
            'setting color space': spaceTimes,
            'setting color': setTimes,
            'getting color': getTimes,
            'getting same color repeatedly': getSameTimes,
            'performing all operations': totalTimes,
        }.items():
            # Convert to dataframe using ms
            df = pd.DataFrame(times) / self.nCalls
            a = df['AttributeSetter']
            b = df['PropertySetter']
            # Calculate descriptives and do a T-test
            T, p = sp.ttest_ind(a, b)
            std = (a.std() + b.std()) / 2
            diff = a.mean() - b.mean()
            # If diff < 0, then attribute setter is faster
            if diff < 0:
                faster = "AttributeSetter"
                slower = "PropertySetter"
            else:
                faster = "PropertySetter"
                slower = "AttributeSetter"
            # Print any significant differences
            if p < 0.05:
                # Construct string to print
                out = (
                    f"{faster} WAS significantly faster than {slower} when {key} "
                    f"(diff: {abs(diff):.2f}ns, T: {T:.2f}, p: {p:.2f})"
                )
            else:
                # Construct string to print
                out = (
                    f"{faster} WAS NOT significantly faster than {slower} when {key}"
                )
            print(out)
