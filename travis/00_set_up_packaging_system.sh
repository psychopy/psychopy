#!/usr/bin/env bash

# Fail script immediately on any errors in external commands,
# and display each line as it gets executed.
set -ev

source ./travis/travis_retry.bash

travis_retry sudo apt-get update -qq
travis_retry sudo apt-get install -qq lsb-release
source /etc/lsb-release
echo ${DISTRIB_CODENAME}
wget -O- https://neuro.debian.net/lists/${DISTRIB_CODENAME}.us-nh.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
wget -q -O- https://neuro.debian.net/_static/neuro.debian.net.asc | sudo apt-key add -
travis_retry sudo apt-get update -qq
sudo apt-cache policy  # What is actually available?
