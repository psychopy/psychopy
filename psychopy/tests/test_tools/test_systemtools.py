import importlib
import importlib.metadata
import platform
import sys

import pytest

from psychopy.tools import systemtools as st


# what the dynamic linker reports loading a `psychtoolbox` built without the
# libraries it links
BROKEN_BUILD_ERROR = (
    "dlopen(/site-packages/psychtoolbox/PsychHID.cpython-312-darwin.so, "
    "0x0002): symbol not found in flat namespace '_libusb_bulk_transfer'")


@pytest.fixture
def appleSilicon(monkeypatch):
    """Make this look like an Apple Silicon Mac."""
    monkeypatch.setattr(sys, 'platform', 'darwin')
    monkeypatch.setattr(platform, 'machine', lambda: 'arm64')


def _installPTB(monkeypatch, installedVersion):
    """Make `installedVersion` look like the installed `psychtoolbox`."""
    realVersion = importlib.metadata.version

    def version(name):
        if name == 'psychtoolbox':
            return installedVersion
        return realVersion(name)

    monkeypatch.setattr(importlib.metadata, 'version', version)


def testDescribesBrokenAppleSiliconBuild(appleSilicon, monkeypatch):
    """A release built from source on Apple Silicon should get upgrade advice.
    """
    _installPTB(monkeypatch, '3.0.19.14')

    description = st.describePsychtoolboxImportError(
        ImportError(BROKEN_BUILD_ERROR))

    assert '3.0.19.14' in description
    assert 'pip install --upgrade "psychtoolbox>=3.0.22.2"' in description
    # and the original error, for anyone who needs the detail
    assert BROKEN_BUILD_ERROR in description


@pytest.mark.parametrize("installedVersion", ['3.0.22.2', '3.0.23.0'])
def testLeavesReleasesWithWheelAlone(appleSilicon, monkeypatch,
                                     installedVersion):
    """A release with an Apple Silicon wheel isn't the known broken build."""
    _installPTB(monkeypatch, installedVersion)

    assert st.describePsychtoolboxImportError(
        ImportError(BROKEN_BUILD_ERROR)) == BROKEN_BUILD_ERROR


@pytest.mark.parametrize("sysPlatform, machine", [
    ('darwin', 'x86_64'), ('linux', 'aarch64'), ('win32', 'AMD64')])
def testLeavesOtherPlatformsAlone(monkeypatch, sysPlatform, machine):
    """Only Apple Silicon gets the broken source build."""
    monkeypatch.setattr(sys, 'platform', sysPlatform)
    monkeypatch.setattr(platform, 'machine', lambda: machine)
    _installPTB(monkeypatch, '3.0.19.14')

    assert st.describePsychtoolboxImportError(
        ImportError(BROKEN_BUILD_ERROR)) == BROKEN_BUILD_ERROR


def testLeavesOtherErrorsAlone(appleSilicon, monkeypatch):
    """An error other than a missing symbol is passed on as it is."""
    _installPTB(monkeypatch, '3.0.19.14')
    err = ModuleNotFoundError("No module named 'psychtoolbox'")

    assert st.describePsychtoolboxImportError(err) == str(err)


def testImportRaisesDescription(appleSilicon, monkeypatch):
    """Importing a broken build should raise with the description."""
    _installPTB(monkeypatch, '3.0.19.14')
    brokenErr = ImportError(BROKEN_BUILD_ERROR)

    def importModule(name):
        raise brokenErr

    monkeypatch.setattr(importlib, 'import_module', importModule)

    with pytest.raises(ImportError, match="pip install --upgrade") as excInfo:
        st.importPsychtoolbox('psychtoolbox.audio')
    assert excInfo.value.__cause__ is brokenErr


def testImportKeepsUndescribedError(monkeypatch):
    """An error with nothing to add is raised unchanged."""
    missingErr = ModuleNotFoundError("No module named 'psychtoolbox'")

    def importModule(name):
        raise missingErr

    monkeypatch.setattr(importlib, 'import_module', importModule)

    with pytest.raises(ModuleNotFoundError) as excInfo:
        st.importPsychtoolbox('psychtoolbox.audio')
    assert excInfo.value is missingErr
