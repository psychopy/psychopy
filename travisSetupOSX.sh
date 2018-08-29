#! /usr/bin/env sh

# Set up the install environment for travis osx

# all we need here is pyo. The rest should come OK from pip dependencies?
brew install liblo libsndfile portaudio portmidi

pip install \
  --install-option="--use-coreaudio" \
  --install-option "--use-double" \
  git+git://github.com/belangeo/pyo.git

# get these done in advance so we can check their version numbers in main script
pip install pyglet matplotlib pillow wxpython openpyxl tables
