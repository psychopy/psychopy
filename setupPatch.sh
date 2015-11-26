#!/bin/sh

echo DID YOU UPDATE THE CHANGELOG?
python setup.py sdist --format=zip
python setup.py egg_info
python setup.py bdist_egg

echo upload to pypi with;
echo python setup.py sdist --format==zip upload
echo python setup.py bdist_egg upload

mv dist/* ../dist
