#!/usr/bin/env bash

# Fail script immediately on any errors in external commands,
# and display each line as it gets executed.
set -ev

source ./travis/travis_retry.bash

# upgrade pip to 9.0.x because 10.0.x says cannot uninstall distutils so --upgrade fails
travis_retry sudo pip install --upgrade -qq pip==9.0.3
echo "Installing PsychoPy dependencies via apt..."
travis_retry sudo apt-get install -qq flac
travis_retry sudo apt-get install -qq libav-tools  # this installs ffmpeg
travis_retry sudo apt-get install -qq python-xlib python-pygame python-opengl
travis_retry sudo apt-get install -qq python-numpy python-scipy python-matplotlib python-pandas
travis_retry sudo apt-get install -qq python-yaml python-lxml python-configobj
travis_retry sudo apt-get install -qq python-imaging python-mock
travis_retry sudo apt-get install -qq python-qt4 python-wxgtk3.0
travis_retry sudo apt-get install -qq python-pyo python-opencv
travis_retry sudo apt-get install -qq python-mock
echo "Installing PsychoPy dependencies via pip..."
sudo pip install requests[security]

travis_retry sudo pip install --upgrade -qq -r requirements_travis.txt
