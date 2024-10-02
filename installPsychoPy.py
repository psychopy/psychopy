#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
"""
Python script to install psychopy including dependencies

NB: At present, for windows and MacOS you may as well just use `pip install psychopy` but
in the future we may add some additional functionality here, like adding application 
shortcuts, checking/recommending virtual envs etc.
"""

# Author: Jonathan Peirce, based on work of Flavio Bastos and Florian Osmani

import os, sys
import pathlib
import subprocess
import os
import sys
import requests

_linux_installer = None  # will be apt-get or yum depending on system

print(
    "This `install_psychopy.py` script is EXPERIMENTAL and may not work!"
    " PsychoPy users have many different systems and it's hard to maintain them all. "
    " Let us know how you get on!\n"
)
if sys.version_info[:2] != (3,10):
    print(
        "PsychoPy is designed for Python 3.10.x "
        f"You are running Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}. "
        "PsychoPy may not work and may not even install!\n"
    )

print(
    "This `install_psychopy.py` script is EXPERIMENTAL and may not work!"
    " PsychoPy users have many different systems and it's hard to maintain them all. "
    " Let us know how you get on!\n"
)

def pip_install(*packages):
    """Install packages using pip."""
    print('Installing packages:', packages)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade'] + list(packages))

def check_venv():
    """Check if this is a virtual environment. If not, recommend quitting and creating one.
    """
    # If this is not a venv then recommend quitting to create one
    if not hasattr(sys, 'real_prefix'):
        print(
            'You should install PsychoPy in a virtual environment,'
            ' to avoid conflicts with other packages, or damaging your system.'
            ' To create a virtual environment in the current directory, run:')
        print('  python3 -m venv .')
        print('Then activate the virtual environment with:')
        print('  source bin/activate')
        print('Then run this script again.')
        response = input('Shall we QUIT now? [y]/n: ')
        if response.lower() != 'n':
            sys.exit(1)

def apt_install(*packages):
    """Install packages using apt, yum, or similar"""
    global _linux_installer
    # check if using this system has apt-get or yum
    if _linux_installer is None:
        for installer in ['apt', 'yum', 'dnf', 'zypper', 'apt-cyg']:
            out = subprocess.run(['which', installer], stdout=subprocess.PIPE)
            if out.returncode == 0:
                _linux_installer = installer
                break
        if _linux_installer is None:
            print('On Linux systems, this script requires either apt-get or yum.')
            sys.exit(1)
            
    def find_package(package):
        # check pacakage name according to apt/yum
        packages_lookup = {
            'python3-dev': {'apt':'libgtk-3-dev', 'yum':'gtk3-devel'},
            'libgtk-3-dev': {'apt':'libgtk-3-dev', 'yum':'gtk3-devel'},
            'libwebkit2gtk-4.0-dev': {'apt':'libwebkit2gtk-4.0-dev', 'yum':'webkit2gtk3-devel'},
            'libxcb-xinerama0': {'apt':'libxcb-xinerama0', 'yum':'libxcb-xinerama'},
            'libegl1-mesa-dev': {'apt':'libegl1-mesa-dev', 'yum':'mesa-libEGL-devel'},
        }
        if package in packages_lookup:
            if _linux_installer in packages_lookup[package]:
                return packages_lookup[package][_linux_installer]
            else:
                return packages_lookup[package]['yum']  # default to yum for dnf, zypper, apt-cyg
        else:
            return package
    packages = [find_package(p) for p in packages]

    print('Installing packages (will require sudo):', packages)
    subprocess.run(['sudo', _linux_installer, 'update'])
    subprocess.run(['sudo', _linux_installer, 'install', '-y'] + list(packages))

if __name__ == "__main__":
    # Check/install builds requirements
    if platform.system() == 'Linux':
        # Install system dependencies
        apt_install(
            'python3-dev',  # need dev in case of compiling C extensions
            'libgtk-3-dev', 'libwebkit2gtk-4.0-dev', # for wxPython
            'libxcb-xinerama0', 'libegl1-mesa-dev', # for OpenGL needs
            'git',  # for push/pull to Pavlovia
            )
        pip_install('-U', 'pip', 'setuptools', 'attrdict')
        print("Next we build wxPython (from source) which takes the longest time."
              " The rest of the installation will automatically continue after and be"
              " much faster.")
        pip_install('wxPython')

    # Install PsychoPy using pip
    pip_install('psychopy')

    print("\nPsychoPy has been installed (or at least attempted). You can now try run it by typing:")
    print("  psychopy")
    print("or:")
    print("  python -m psychopy.app.psychopyApp")
    print("You may need to activate the virtual environment first though.")
