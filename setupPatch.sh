#!/bin/sh

echo DID YOU UPDATE THE CHANGELOG?
sudo python setup.py sdist --format=zip
sudo python setup.py egg_info
sudo python setup.py bdist_egg

echo register with;
echo sudo python setup.py register

mv dist/* ../dist
