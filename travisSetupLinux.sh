#!/bin/bash

travis_retry() {
  local result=0
  local count=1
  while [ $count -le 3 ]; do
    [ $result -ne 0 ] && {
      echo -e "\n${ANSI_RED}The command \"$@\" failed. Retrying, $count of 3.${ANSI_RESET}\n" >&2
    }
    "$@"
    result=$?
    [ $result -eq 0 ] && break
    count=$(($count + 1))
    sleep 1
  done

  [ $count -gt 3 ] && {
    echo -e "\n${ANSI_RED}The command \"$@\" failed 3 times.${ANSI_RESET}\n" >&2
  }

  return $result
}

# Set up the install environment for travis linux installations

travis_retry sudo apt-get update -qq
travis_retry sudo apt-get install -qq lsb-release
source /etc/lsb-release
echo ${DISTRIB_CODENAME}
wget -O- http://neuro.debian.net/lists/${DISTRIB_CODENAME}.us-nh.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
wget -q -O- http://neuro.debian.net/_static/neuro.debian.net.asc | sudo apt-key add -
travis_retry sudo apt-get update -qq
sudo apt-cache policy  # What is actually available?

travis_retry sudo apt-get install -qq xpra xserver-xorg-video-dummy

travis_retry sudo apt-get install -qq xvfb xauth libgl1-mesa-dri libavbin0
travis_retry sudo apt-get install -qq libportaudio2
travis_retry sudo apt-get install -qq flac
travis_retry sudo apt-get install -qq libav-tools  # this install ffmpeg
travis_retry sudo apt-get install -qq libwebkitgtk-1.0-0
flac -version

# Locales
# - travis_retry sudo apt-get install -qq language-pack-en-base  # English locales
travis_retry sudo apt-get install -qq language-pack-ja-base  # Japanese locale
# - sudo dpkg-reconfigure locales
# - locale -a  # list available locales

travis_retry sudo apt-get install -qq libasound2-dev alsa-utils alsa-oss
sudo modprobe snd-dummy
sudo lsmod

# upgrade pip to 9.0.x because 10.0.x says cannot uninstall distutils so --upgrade fails
if [ -z $ANACONDA ]; then travis_retry sudo pip install --upgrade -qq pip==9.0.3; fi

if [ -z $ANACONDA ]; then
  echo "Installing PsychoPy dependencies via apt...";
  travis_retry sudo apt-get install -qq python-xlib python-pygame python-opengl;
  travis_retry sudo apt-get install -qq python-numpy python-scipy python-matplotlib python-pandas;
  travis_retry sudo apt-get install -qq python-yaml python-lxml python-configobj;
  travis_retry sudo apt-get install -qq python-imaging python-mock;
  travis_retry sudo apt-get install -qq python-qt4;
  travis_retry sudo apt-get install -qq python-pyo python-opencv;
  travis_retry sudo apt-get install -qq python-mock;

fi


if [ -n "$ANACONDA" ]; then
  echo "Installing Miniconda environment...";
  wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
  bash miniconda.sh -b -p $HOME/miniconda;
  export PATH="$HOME/miniconda/bin:$PATH";
  hash -r;
  conda config --set always_yes yes --set changeps1 no;
fi

if [ -n "$ANACONDA" ]; then conda update -q conda; fi
if [ -n "$ANACONDA" ]; then conda info -a; fi
if [ -n "$ANACONDA" ]; then ls -la ./conda/environment-$TRAVIS_PYTHON_VERSION.yml; fi
if [ -n "$ANACONDA" ]; then conda env create -n psychopy-conda -f ./conda/environment-$TRAVIS_PYTHON_VERSION.yml; fi
if [ -n "$ANACONDA" ]; then conda env list; fi
if [ -n "$ANACONDA" ]; then source activate psychopy-conda; fi
if [ -n "$ANACONDA" ]; then if [ -n "$WXPYTHON" ]; then conda install wxpython=$WXPYTHON; fi; fi
if [ -n "$ANACONDA" ]; then if [ -n "$OPENPYXL" ]; then conda install openpyxl=$OPENPYXL; fi; fi

echo "Installing PsychoPy dependencies via pip...";
sudo pip install requests[security];
sudo pip install --upgrade -qq -r requirements_travis.txt;
