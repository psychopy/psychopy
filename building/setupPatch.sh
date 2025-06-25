#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
python3 ../building/semanticVersion.py --write-git-sha --write-version
python3 -m build
echo register with twine
