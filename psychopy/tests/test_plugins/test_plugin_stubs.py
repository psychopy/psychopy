from http.client import RemoteDisconnected
import importlib
import pytest
import requests
from psychopy import logging
from psychopy.plugins import PluginStub


def test_plugin_stub_docs():
    """
    Test that links (docsHome and docsRef) are combined correctly in the docstring of PluginStub
    """
    cases = [
        # docsHome with no docsRef
        {
            'plugin': "psychopy-test",
            'docsHome': "https://psychopy.org",
            'docsRef': "",
            'ans': {
                'docsHome': "https://psychopy.org",
                'docsLink': "https://psychopy.org/",
            } 
        },
        # docsHome included in docsRef
        {
            'plugin': "psychopy-test",
            'docsHome': "https://psychopy.org",
            'docsRef': "https://psychopy.org/test",
            'ans': {
                'docsHome': "https://psychopy.org",
                'docsLink': "https://psychopy.org/test",
            } 
        },
        # docsRef without /
        {
            'plugin': "psychopy-test",
            'docsHome': "https://psychopy.org",
            'docsRef': "test",
            'ans': {
                'docsHome': "https://psychopy.org",
                'docsLink': "https://psychopy.org/test",
            } 
        },
        # docsHome with /
        {
            'plugin': "psychopy-test",
            'docsHome': "https://psychopy.org/",
            'docsRef': "/test",
            'ans': {
                'docsHome': "https://psychopy.org",
                'docsLink': "https://psychopy.org/test",
            } 
        },
    ]

    for case in cases:
        # subclass PluginStub with the given values
        class TestPluginStub(
            PluginStub,
            plugin=case['plugin'],
            docsHome=case['docsHome'],
            docsRef=case['docsRef'],
        ):
            pass
        # check for the necessary strings in its docstr
        assert case['plugin'] in TestPluginStub.__doc__
        assert "<%(docsHome)s>" % case['ans'] in TestPluginStub.__doc__
        assert "<%(docsLink)s>" % case['ans'] in TestPluginStub.__doc__


def test_plugin_stub_links():
    # import modules with PluginStubs in them
    knownStubModules = [
        "psychopy.microphone",
        "psychopy.hardware.cedrus",
        "psychopy.hardware.emulator",
        "psychopy.hardware.gammasci",
        "psychopy.hardware.minolta",
        "psychopy.hardware.minolta",
        "psychopy.hardware.pr",
        "psychopy.hardware.crs.bits",
        "psychopy.hardware.crs.optical",
        "psychopy.hardware.crs.shaders",
        "psychopy.visual.movie2",
        "psychopy.visual.movie3",
        "psychopy.visual.noise",
        "psychopy.visual.patch",
        "psychopy.visual.radial",
        "psychopy.visual.ratingscale",
        "psychopy.visual.secondorder",
        "psychopy.hardware.brainproducts",
        "psychopy.hardware.forp",
        "psychopy.hardware.iolab",
        "psychopy.hardware.labjacks",
        "psychopy.hardware.qmix",
        "psychopy.hardware.bbtk",
        "psychopy.sound.backend_pyo",
        "psychopy.sound.backend_sounddevice",
        "psychopy.visual.backends.glfwbackend",
    ]
    for stubModule in knownStubModules:
        importlib.import_module(stubModule)
    # check for an internet connection in general
    resp = requests.get("https://psychopy.org")
    if not resp.ok:
        pytest.skip()
    # iterate through subclasses of PluginStub
    for cls in PluginStub.__subclasses__():
        # skip PluginStubs from the test suite
        if cls.__module__.startswith("psychopy.tests"):
            continue
        # get pages from web
        try:
            docsHome = requests.get(cls.docsHome)
            docsLink = requests.get(cls.docsLink)
        except RemoteDisconnected:
            # skip test if there's a connection error
            pytest.skip()
        # check that we got some content
        assert docsHome.ok, (
            f"No documentation found at {cls.docsHome} (PluginStub for {cls.__module__}:{cls.__name__})"
        )
        assert docsLink.ok, (
            f"No documentation found at {cls.docsLink} (PluginStub for {cls.__module__}:{cls.__name__})"
        )
