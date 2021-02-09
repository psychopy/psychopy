#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
python3.6 setup.py sdist --format=zip
python3.6 setup.py egg_info
# python setup.py bdist_wheel --universal

echo register with;
echo twine upload ../dist/

mv dist/* ../dist
