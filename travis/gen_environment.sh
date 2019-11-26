#!/bin/sh

# Create environment.yml without version numbers and installation prefix
conda env export | cut -f 1 -d '=' | grep -v "^prefix: " > environment.yml
