#!/bin/sh

echo DID YOU UPDATE THE CHANGELOG?
python setup.py sdist --format=zip
python setup.py egg_info
python setup.py bdist_egg

echo register with;
echo python setup.py register

mv dist/* ../dist
