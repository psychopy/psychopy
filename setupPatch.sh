#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
python3.8 -c 'from building import createGitShaFile; createGitShaFile.createGitShaFile())'
pdm build
echo register with twine
