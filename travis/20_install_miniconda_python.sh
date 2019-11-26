#!/usr/bin/env bash

# Fail script immediately on any errors in external commands,
# and display each line as it gets executed.
set -ev

echo "Installing Miniconda environment..."
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
source ~/miniconda/etc/profile.d/conda.sh # Initialize shell.
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
ls -la ./travis/environment-$PYTHON_VERSION.yml
conda env create -n psychopy-conda -f ./travis/environment-$PYTHON_VERSION.yml
conda env list
conda activate psychopy-conda
if [ -n "$WXPYTHON" ]; then conda install --freeze-installed -c conda-forge wxpython=$WXPYTHON; fi
if [ -n "$OPENPYXL" ]; then conda install --freeze-installed -c conda-forge openpyxl=$OPENPYXL; fi
if [ -n "$PYGLET" ]; then conda install --freeze-installed -c conda-forge pyglet=$PYGLET; fi
conda list # Display all installed packages.
