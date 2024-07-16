#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import subprocess
import os
import sys
import requests

"""This script will install PsychoPy to the current Python environment. 

For Linux installations, the script will fetch the supported linux distros for wxPython 
and interactively select the distro and version to download the appropriate .whl file.

After that the script will install PsychoPy using pip.

NB: At present, for windows and MacOS you may as well just use `pip install psychopy` but
in the future we may add some additional functionality here, like adding application 
shortcuts, checking/recommending virtual envs etc.
"""

# Author: Florian Osmani
# Author: Jonathan Peirce

wxLinuxUrl = "https://extras.wxpython.org/wxPython4/extras/linux/gtk3/"

def installWhlFile(whlUrl):
    """Installs a single specified wheel file using pip"""
    wheel_path = os.path.basename(whlUrl)
    subprocess.run([sys.exectuable, '-m', 'pip', 'install', '-U', '-f', wheel_path, 'wxPython'], check=True)

def installPsychoPy():
    """Runs pip install psychopy"""
    subprocess.run([sys.exectuable, '-m', 'pip', 'install', 'psychopy'], check=True)

def getWxUrl(distroNames=None):
    """Fetch the supported linux distros for wx and interactively select the 
    distro and version to download the appropriate .whl file.

    Args:
        distroNames (_type_, optional): _description_. Defaults to None.

    Returns:
        list: URL of the wheel for the selected distro/version
    """    
    def extractDistroNames(url):
        """Extract the names of the linux distributions from the html content"""

        response = requests.get(url)
        response.raise_for_status()

        distro_names = []
        lines = response.text.split('\n')
        for line in lines:
            if '<a href="' in line and '/"' in line:
                start_index = line.find('<a href="') + len('<a href="')
                end_index = line.find('/"', start_index)
                distro_name = line[start_index:end_index]
                distro_names.append(distro_name)
        return distro_names
    
    def saveDistroData(distro_names, filename):
        """Saves text file with distro names if needed for future use"""
        with open(filename, 'w') as file:
            for distro_name in distro_names:
                file.write(distro_name + '\n')
                
    def getWxSupportedDistros(outfile=None):
        """Find all the linux distributions tha twxPython has wheels for"""
        distro_names = extractDistroNames(wxLinuxUrl)
        if outfile:
            saveDistroData(distro_names, outfile)
            print(f"Distro data saved to {outfile}")
        return distro_names

    if distroNames is None:
        distroNames = getWxSupportedDistros()
    version_info = sys.version_info
    if version_info.minor < 8 or version_info.minor > 10:
        print("Sorry, please use Python 3.8, 3.9, or 3.10 to install Psychopy")
        return None

    python_cp = f"cp{version_info.major}{version_info.minor}"

    def selectDistro(distroNames):
        print("Please select your Linux distribution:")
        for i, distro in enumerate(distroNames):
            print(f"{i + 1}. {distro}")

        while True:
            choice = input("Enter your choice (number): ")
            if choice.isdigit() and 1 <= int(choice) <= len(distroNames):
                return distroNames[int(choice) - 1]
            else:
                print("Invalid choice, please try again.")

    def organizeDistributions(distroNames):
        distroDict = {}
        for distro in distroNames:
            nameParts = distro.split('-')
            distroName = '-'.join(nameParts[:-1])
            version = nameParts[-1] if len(nameParts) > 1 else 'default'

            if distroName in distroDict:
                distroDict[distroName].append(version)
            else:
                distroDict[distroName] = [version]

        return distroDict

    def selectVersion(selectedDistro, versions):
        while True:
            print("Please select the version:")
            for i, version in enumerate(versions):
                print(f"{i + 1}. {selectedDistro}-{version}")
            print("0. Go back")

            choice = input("Enter your choice (number): ")
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(versions):
                    return versions[choice - 1]
                elif choice == 0:
                    return None
            print("Invalid choice, please try again.")

    def fetchWhlFiles(htmlContent, pythonVersions):
        all = []
        recommended = []
        lines = htmlContent.split('\n')
        for line in lines:
            if '<a href="' in line and '.whl"' in line:
                start_index = line.find('<a href="') + len('<a href="')
                end_index = line.find('"', start_index)
                whl_file = line[start_index:end_index]
                all.append(whl_file)
                if pythonVersions in line:
                    recommended.append(whl_file)
        return recommended, all

    organizedDistros = organizeDistributions(distroNames)

    # go through the process of selecting the distro and version and
    # return the url of the .whl file when the user has decided
    while True:
        selectedDistro = selectDistro(list(organizedDistros.keys()))
        print(f"You have selected the distribution: {selectedDistro}")

        selectedVersion = selectVersion(selectedDistro, organizedDistros[selectedDistro])
        if selectedVersion is None:
            print("Going back to distro selection...")
            continue

        print(f"You have selected version: {selectedDistro}-{selectedVersion}")

        distroUrl = f"{wxLinuxUrl}{selectedDistro}-{selectedVersion}/"
        print(f"Found valid .whl files at: {distroUrl}")

        response = requests.get(distroUrl)
        response.raise_for_status()
        htmlThisDistro = response.text

        recommended, all = fetchWhlFiles(htmlThisDistro, pythonVersions=python_cp)

        if recommended:
            return distroUrl + recommended[-1]
        else:
            if all:
                print(f"No .whl files for python {python_cp}")
                allPretty = '\n- '+('\n- '.join(all))
                print(f"Found the following .whl files at {distroUrl}:{allPretty}")
            else:
                print(f"No .whl files found at {distroUrl}")


if __name__ == "__main__":
    # install wxPython
    wxWhl = getWxUrl()  # for linux fetches the supported distros and interactively selects the distro and version
    if wxWhl:
        installWhlFile(wxWhl)

    # then install the rest of psychopy
    installPsychoPy()