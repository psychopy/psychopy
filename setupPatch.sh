#!/bin/sh

echo DID YOU UPDATE THE CHANGELOG?
python setup.py sdist --format=zip
python setup.py egg_info
# python setup.py bdist_wheel --universal

echo register with;
echo twine upload ../dist/

mv dist/* ../dist
