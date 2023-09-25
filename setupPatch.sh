#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
python3.8 -c 'from building import createInitFile; createInitFile.createInitFile(dist="sdist")'
pdm build
python3.8 -c 'from building import createInitFile; createInitFile.createInitFile(dist=None)'
echo register with twine
