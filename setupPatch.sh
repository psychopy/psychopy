#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
python3 building/writeVersionFiles.py
python3 -m build
echo register with twine
