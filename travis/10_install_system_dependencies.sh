#!/usr/bin/env bash

# Fail script immediately on any errors in external commands,
# and display each line as it gets executed.
set -ev

source ./travis/travis_retry.bash

# This might come in handy once we switch to Trusty, as its Xvfb
# doesn't properly support the RANDR extension
# - travis_retry sudo apt-get install -qq xpra xserver-xorg-video-dummy

travis_retry sudo apt-get install -qq xvfb xauth libgl1-mesa-dri libavbin0
travis_retry sudo apt-get install -qq libportaudio2
travis_retry sudo apt-get install -qq libwebkitgtk-1.0-0

# Locales
# - travis_retry sudo apt-get install -qq language-pack-en-base  # English locales
travis_retry sudo apt-get install -qq language-pack-ja-base  # Japanese locale
# - sudo dpkg-reconfigure locales
# - locale -a  # list available locales

travis_retry sudo apt-get install -qq libasound2-dev alsa-utils alsa-oss
sudo modprobe snd-dummy
sudo lsmod
