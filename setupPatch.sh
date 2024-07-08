#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
python3 -c 'from building import createGitShaFile; createGitShaFile.createGitShaFile()'
python3 -m build
echo register with twine
